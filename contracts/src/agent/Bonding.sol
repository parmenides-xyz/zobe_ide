// SPDX-License-Identifier: MIT
// Modified from https://github.com/sourlodine/Pump.fun-Smart-Contract/blob/main/contracts/PumpFun.sol
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts-upgradeable/utils/ReentrancyGuardUpgradeable.sol";

import "./interfaces/IUniswapFactory.sol";
import "./interfaces/IUniswapRouter.sol";


import "./FFactory.sol";
import "./IFPair.sol";
import "./FRouter.sol";
import "./FERC20.sol";
import "./WVIRTUAL.sol";

contract Bonding is
    Initializable,
    ReentrancyGuardUpgradeable,
    OwnableUpgradeable
{
    using SafeERC20 for IERC20;

    FFactory public factory;
    FRouter public router;
    WVIRTUAL public wvirtual;
    IUniswapFactory public uniswapFactory;
    IUniswapRouter public uniswapRouter;

    uint256 public initialSupply;
    uint256 public assetLaunchFee;
    uint256 public virtualLaunchFee;
    uint256 public virtualGradThreshold;
    uint256 public assetGradThreshold;
    uint256 public maxTx; // Max amount of token that can be bought at once, as a percentage.
    uint256 uniswapTaxBps; // Tax rate on swaps (post graduation), in BPS (100 = 1%)


    struct Profile {
        address user;
        address[] tokens;
    }

    struct Token {
        address creator;
        address token;
        address pair;
        Data data;
        bool trading;
        bool tradingOnUniswap;
    }

    struct Data {
        address token;
        string name;
        string _name;
        string ticker;
        uint256 supply;
        uint256 price;
        uint256 marketCap;
        uint256 liquidity;
        uint256 volume;
        uint256 volume24H;
        uint256 prevPrice;
        uint256 lastUpdated;
    }


    mapping(address => Profile) public profile;
    address[] public profiles;

    mapping(address => Token) public tokenInfo;
    address[] public tokenInfos;

    uint256 public graduationSlippage; // 5% slippage default

    event Launched(address indexed token, address indexed pair, uint);
    event Deployed(address indexed token, uint256 amount0, uint256 amount1);
    event Graduated(address indexed token, address indexed pair);

    receive() external payable {}
    
    // Initializes the Bonding contract with the given parameters.
    function initialize(
        address factory_,
        address router_,
        address payable wvirtual_,
        uint256 assetLaunchFee_,
        uint256 virtualLaunchFee_,
        uint256 initialSupply_,
        uint256 maxTx_,
        uint256 graduationSlippage_,
        uint256 virtualGradThreshold_,
        uint256 assetGradThreshold_,
        uint256 uniswapTaxBps_,
        address uniswapFactory_,
        address uniswapRouter_
    ) external initializer {
        __ReentrancyGuard_init();
        __Ownable_init(msg.sender);

        factory = FFactory(factory_);
        router = FRouter(router_);
        wvirtual = WVIRTUAL(wvirtual_);

        assetLaunchFee = assetLaunchFee_;
        virtualLaunchFee = virtualLaunchFee_;

        initialSupply = initialSupply_;
        maxTx = maxTx_;
        graduationSlippage = graduationSlippage_;
        virtualGradThreshold = virtualGradThreshold_;
        assetGradThreshold = assetGradThreshold_;
        uniswapTaxBps = uniswapTaxBps_;

        uniswapFactory = IUniswapFactory(uniswapFactory_);
        uniswapRouter = IUniswapRouter(uniswapRouter_);
    }

    function _createUserProfile(address _user) internal returns (bool) {
        address[] memory _tokens;

        Profile memory _profile = Profile({user: _user, tokens: _tokens});

        profile[_user] = _profile;

        profiles.push(_user);

        return true;
    }

    function _checkIfProfileExists(address _user) internal view returns (bool) {
        return profile[_user].user == _user;
    }

    function _approval(
        address _spender,
        address _token,
        uint256 amount
    ) internal returns (bool) {
        IERC20(_token).forceApprove(_spender, amount);

        return true;
    }

    function setInitialSupply(uint256 newSupply) public onlyOwner {
        initialSupply = newSupply;
    }

    function setVirtualGradThreshold(uint256 newThreshold) public onlyOwner {
        virtualGradThreshold = newThreshold;
    }

    function setAssetGradThreshold(uint256 newThreshold) public onlyOwner {
        assetGradThreshold = newThreshold;
    }

    // Defines the amount of assetToken required to launch a token
    function setAssetLaunchFee(uint256 newFee) public onlyOwner {
        assetLaunchFee = newFee;
    }

    // Defines the amount of VIRTUAL required to launch a token
    function setVirtualLaunchFee(uint256 newFee) public onlyOwner {
        virtualLaunchFee = newFee;
    }

    function setMaxTx(uint256 maxTx_) public onlyOwner {
        maxTx = maxTx_;
    }

    function setGraduationSlippage(uint256 slippage_) public onlyOwner {
        graduationSlippage = slippage_;
    }


    function getUserTokens(
        address account
    ) public view returns (address[] memory) {
        require(_checkIfProfileExists(account), "User Profile dose not exist.");

        Profile memory _profile = profile[account];

        return _profile.tokens;
    }

    // Method for launching a new token, using another ERC20 token as the paired token in the pool.
    function launchWithAsset(
        string memory _name,
        string memory _ticker,
        uint256 purchaseAmount,
        address assetToken
    ) public nonReentrant returns (address, address, uint) {
        require(
            purchaseAmount >= assetLaunchFee,
            "Purchase amount must be greater than or equal to fee"
        );
        require(
            IERC20(assetToken).balanceOf(msg.sender) >= purchaseAmount,
            "Insufficient amount"
        );
        uint256 initialPurchase = (purchaseAmount - assetLaunchFee);
        IERC20(assetToken).safeTransferFrom(
            msg.sender,
            address(this),
            purchaseAmount
        );

        return _launch(_name, _ticker, assetToken, initialPurchase, assetLaunchFee);       
    }

    function _launch(string memory _name, string memory _ticker, address assetToken, uint256 initialPurchase, uint256 initialLiquidity) private returns (address, address, uint) {
        // Create the new token
        FERC20 token = new FERC20(_name, _ticker, initialSupply, maxTx);
        uint256 supply = token.totalSupply();

        address _pair = factory.createPair(address(token), assetToken);

        // Ensure the router can spend all of it so it can deposit the tokens into the pool
        bool approved = _approval(address(router), address(token), supply);
        require(approved);

        // Ensure the router can use all of the input assetToken as well
        IERC20(assetToken).forceApprove(address(router), initialPurchase + initialLiquidity);

        // Seed the pool with all the new token, and the initialLiquidity (fee)
        router.addInitialLiquidity(address(token), assetToken, supply, initialLiquidity);

        // Set up all the token data based on the initialLiquidity added
        Data memory _data = Data({
            token: address(token),
            name: _name,
            _name: _name,
            ticker: _ticker,
            supply: supply,
            price: supply / initialLiquidity,
            marketCap: initialLiquidity,
            liquidity: initialLiquidity * 2,
            volume: 0,
            volume24H: 0,
            prevPrice: supply / initialLiquidity,
            lastUpdated: block.timestamp
        });

        Token memory tmpToken = Token({
            creator: msg.sender,
            token: address(token),
            pair: _pair,
            data: _data,
            trading: true, // Can only be traded once creator made initial purchase
            tradingOnUniswap: false
        });

        tokenInfo[address(token)] = tmpToken;
        tokenInfos.push(address(token));

        bool exists = _checkIfProfileExists(msg.sender);

        if (exists) {
            Profile storage _profile = profile[msg.sender];

            _profile.tokens.push(address(token));
        } else {
            bool created = _createUserProfile(msg.sender);

            if (created) {
                Profile storage _profile = profile[msg.sender];

                _profile.tokens.push(address(token));
            }
        }

        uint n = tokenInfos.length;

        emit Launched(address(token), _pair, n);

        // Make initial purchase
        if (initialPurchase > 0) {
            buy(initialPurchase, address(token), assetToken, 0);
        }

        return (address(token), _pair, n);
    }

    // Sells the given token (at tokenAddress) in exchange for assetToken.
    // This token must have been launched using assetToken.
    function sellForAsset(
        uint256 amountIn,
        address tokenAddress,
        address assetToken,
        uint256 amountOutMin
    ) public returns (uint256 amountReceived) {
        require(assetToken != address(wvirtual), "Call sellForVirtual for dealing with wvirtual");
        return sell(amountIn, tokenAddress, assetToken, amountOutMin);
    }

    function sell(
        uint256 amountIn,
        address tokenAddress,
        address assetToken,
        uint256 amountOutMin
    ) private returns (uint256 amountReceived) {
        require(tokenInfo[tokenAddress].trading, "Token not trading");

        address pairAddress = factory.getPair(
            tokenAddress,
            assetToken
        );

        IFPair pair = IFPair(pairAddress);

        (uint256 reserveA, uint256 reserveB) = pair.getReserves();

        FERC20(tokenAddress).transferFrom(msg.sender, address(this), amountIn);
        FERC20(tokenAddress).approve(address(router), 0);
        FERC20(tokenAddress).approve(address(router), amountIn);

        // If assetToken is wvirtual, the bonding token contract has to convert it back to VIRTUAL before sending it back to the user.
        address recipient;
        if (assetToken == address(wvirtual)) {
            recipient = address(this);
        } else {
            recipient = msg.sender;
        }

        (uint256 amount0In, uint256 amount1Out, uint256 _amountReceived) = router.sell(
            amountIn,
            tokenAddress,
            assetToken,
            recipient
        );

        require(_amountReceived >= amountOutMin, "Insufficient output amount");

        uint256 newReserveA = reserveA + amount0In;
        uint256 newReserveB = reserveB - amount1Out;
        uint256 duration = block.timestamp -
            tokenInfo[tokenAddress].data.lastUpdated;

        uint256 liquidity = newReserveB * 2;
        uint256 mCap = (tokenInfo[tokenAddress].data.supply * newReserveB) /
            newReserveA;

        uint256 price = newReserveA / newReserveB;
        uint256 volume = duration > 86400
            ? amount1Out
            : tokenInfo[tokenAddress].data.volume24H + amount1Out;
        uint256 prevPrice = duration > 86400
            ? tokenInfo[tokenAddress].data.price
            : tokenInfo[tokenAddress].data.prevPrice;

        tokenInfo[tokenAddress].data.price = price;
        tokenInfo[tokenAddress].data.marketCap = mCap;
        tokenInfo[tokenAddress].data.liquidity = liquidity;
        tokenInfo[tokenAddress].data.volume =
            tokenInfo[tokenAddress].data.volume +
            amount1Out;
        tokenInfo[tokenAddress].data.volume24H = volume;
        tokenInfo[tokenAddress].data.prevPrice = prevPrice;

        if (duration > 86400) {
            tokenInfo[tokenAddress].data.lastUpdated = block.timestamp;
        }

        return _amountReceived;
    }


    // Buys the given token (at tokenAddress) in exchange for assetToken.
    // This token must have been launched using assetToken.

    // Transfers asset tokens from user to this contract, then executes the buy
    function buyWithAsset(
        uint256 amountIn,
        address tokenAddress,
        address assetToken,
        uint256 amountOutMin
    ) public returns (bool) {
        uint256 currBal = IERC20(assetToken).balanceOf(msg.sender);

        require(currBal >= amountIn, "Insufficient asset token");

        // Transfer assetToken to Bonding contract from user
        IERC20(assetToken).safeTransferFrom(msg.sender, address(this), amountIn);

        return buy(amountIn, tokenAddress, assetToken, amountOutMin);
    }

    function buy(
        uint256 amountIn,
        address tokenAddress,
        address assetToken,
        uint256 amountOutMin
    ) private returns (bool) {
        require(tokenInfo[tokenAddress].trading, "Token not trading");

        address pairAddress = factory.getPair(
            tokenAddress,
            assetToken
        );

        IFPair pair = IFPair(pairAddress);

        (uint256 reserveA, uint256 reserveB) = pair.getReserves();

        // Approve router to spend asset token on behalf of Bonding
        SafeERC20.forceApprove(
            IERC20(assetToken),
            address(router),
            amountIn
        );
        
        (uint256 amount1In, uint256 amount0Out) = router.buy(
            amountIn,
            tokenAddress,
            assetToken,
            msg.sender
        );

        require(
            amount0Out >= amountOutMin,
            "Insufficient output amount"
        );

        uint256 newReserveA = reserveA - amount0Out;
        uint256 newReserveB = reserveB + amount1In;
        uint256 duration = block.timestamp -
            tokenInfo[tokenAddress].data.lastUpdated;

        uint256 liquidity = newReserveB * 2;
        uint256 mCap = (tokenInfo[tokenAddress].data.supply * newReserveB) /
            newReserveA;
        uint256 price = newReserveA / newReserveB;
        uint256 volume = duration > 86400
            ? amount1In
            : tokenInfo[tokenAddress].data.volume24H + amount1In;
        uint256 _price = duration > 86400
            ? tokenInfo[tokenAddress].data.price
            : tokenInfo[tokenAddress].data.prevPrice;

        tokenInfo[tokenAddress].data.price = price;
        tokenInfo[tokenAddress].data.marketCap = mCap;
        tokenInfo[tokenAddress].data.liquidity = liquidity;
        tokenInfo[tokenAddress].data.volume =
            tokenInfo[tokenAddress].data.volume +
            amount1In;
        tokenInfo[tokenAddress].data.volume24H = volume;
        tokenInfo[tokenAddress].data.prevPrice = _price;

        if (duration > 86400) {
            tokenInfo[tokenAddress].data.lastUpdated = block.timestamp;
        }

        // If sufficient tokens has been deposited, graduate this token
        uint256 gradThreshold;
        if (assetToken == address(wvirtual)) {
            gradThreshold = virtualGradThreshold;
        } else {
            gradThreshold = assetGradThreshold;
        }

        if (pair.assetBalance() >= gradThreshold && tokenInfo[tokenAddress].trading) {
            _graduateToken(tokenAddress, assetToken);
        }

        return true;
    }

    /// @notice Buy a bonding token using VIRTUAL
    function buyWithVirtual(address tokenAddress, uint256 amountOutMin) public payable returns (bool) {
        require(msg.value > 0, "Must send VIRTUAL");

        // Step 1: Wrap VIRTUAL into WVIRTUAL
        wvirtual.deposit{value: msg.value}();

        // Step 2: Approve router to spend WVIRTUAL
        wvirtual.approve(address(router), msg.value);

        // Step 3: Execute existing ERC-20 buy logic
        return buy(msg.value, tokenAddress, address(wvirtual), amountOutMin);
    }

    /// @notice Sell a bonding token and receive VIRTUAL
    function sellForVirtual(uint256 amountIn, address tokenAddress, uint256 amountOutMin) public nonReentrant returns (bool) {
        require(tokenInfo[tokenAddress].trading, "Token not trading");

        // Step 1: Approve router to spend user's bonding token
        FERC20(tokenAddress).forceApprove(address(router), amountIn);

        // Step 2: Perform the sell (sends WVIRTUAL to this contract)
        uint256 amountReceived = sell(amountIn, tokenAddress, address(wvirtual), amountOutMin);

        // Step 3: Unwrap WVIRTUAL and send VIRTUAL back to user
        wvirtual.withdraw(amountReceived);

        payable(msg.sender).transfer(amountReceived);

        return true;
    }

    /// @notice Launch a bonding token that uses VIRTUAL as it's asset pair
    function launchWithVirtual(string memory _name, string memory _ticker) public payable returns (address, address, uint) {
        require(
            msg.value >= virtualLaunchFee,
            "Purchase amount must be greater than or equal to fee"
        );

        // Step 1: Wrap VIRTUAL into WVIRTUAL
        wvirtual.deposit{value: msg.value}();

        uint256 initialPurchase = (msg.value - virtualLaunchFee);

        // Step 2: Execute existing ERC-20 launch logic
        return _launch(_name, _ticker, address(wvirtual), initialPurchase, virtualLaunchFee);
    }


    // Helper function that is called when the token hits its graduation threshold.
    // 1. Pulls liquidity from the currently deployed pool
    // 2. Creates a new pool on Uniswap
    // 3. Deposits all the assetToken as well as a proportionate amount of token from the pool so that price remains the same on Uniswap
    // 4. Burns the remaining token that was not deposited in the pool.

    function _graduateToken(address tokenAddress, address assetToken) private {
        Token storage _token = tokenInfo[tokenAddress];

        require(_token.trading && !_token.tradingOnUniswap, "Already graduated");

        _token.trading = false;
        _token.tradingOnUniswap = true;

        // 1. Pull liquidity from bonding pool and deposit into Uniswap

        // Transfer assets from old pool to this contract
        (uint256 tokenAmount, uint256 assetAmount) = router.graduatePool(tokenAddress, assetToken); // Sends assetToken to Bonding contract

        // Approve router
        SafeERC20.forceApprove(
            IERC20(tokenAddress),
            address(uniswapRouter),
            tokenAmount
        );
        SafeERC20.forceApprove(
            IERC20(assetToken),
            address(uniswapRouter),
            assetAmount
        );

        // If assetToken is wvirtual, swap back for regular VIRTUAL before depositing to pool
        address uniswapAsset;
        if (assetToken == address(wvirtual)) {
            uniswapAsset = uniswapRouter.WVIRTUAL();
            wvirtual.withdraw(assetAmount);
            // addLiquidity automatically creates the pool if it doesn't exist
            uniswapRouter.addLiquidityVIRTUAL{value: assetAmount}(tokenAddress, tokenAmount, tokenAmount * (100-graduationSlippage) / 100, assetAmount * (100-graduationSlippage) / 100, address(this), block.timestamp + 600);
        } else {
            uniswapAsset = assetToken;
            // Add liquidity to Uniswap. This sends an NFT back to this contract that we have to lock up somehow.
            uniswapRouter.addLiquidity(
                tokenAddress,
                uniswapAsset,
                tokenAmount,
                assetAmount,
                tokenAmount * (100-graduationSlippage) / 100, // slippage min
                assetAmount * (100-graduationSlippage) / 100,
                address(this),
                block.timestamp + 600
            );
        }

        address uniswapPair = uniswapFactory.getPair(tokenAddress, uniswapAsset);
        _token.pair = uniswapPair;

        address taxVault = factory.taxVault();
        FERC20(tokenAddress).updateTaxSettings(taxVault, uniswapTaxBps);
        FERC20(tokenAddress).setIsIncludedInTax(uniswapPair);

        emit Graduated(tokenAddress, uniswapPair);
    }

/// HELPER QUERY FUNCTIONS ///

    // Calculate the maximum that can be sent at launch, based on the initalSupply, tax and fees.
    function getMaxLaunchInputAsset() public view returns (uint256 maxInput) {
        return getMaxLaunchInput(assetLaunchFee);
    }

    // Calculate the maximum that can be sent at launch, based on the initalSupply, tax and fees.
    function getMaxLaunchInputVirtual() public view returns (uint256 maxInput) {
        return getMaxLaunchInput(virtualLaunchFee);
    }

    function getMaxLaunchInput(uint256 launchFee) private view returns (uint256 maxInput) {
        uint multiplier = factory.multiplier();
        uint256 syntheticAssets = multiplier * launchFee;
        uint256 maxBuy = maxBuyInput(initialSupply, maxTx, initialSupply, syntheticAssets);

        // Add flat fee back
        maxInput = maxBuy + launchFee; 
    }

    // Gets the maximum input to a buy using VIRTUAL at this point given the tokens max tx, supply and balances.
    function getMaxBuyInputVirtual(address token) public view returns (uint256 maxInput) {
        return getMaxBuyInputAsset(token, address(wvirtual));
    }

    // Gets the maximum input to a buy at this point given the tokens max tx, supply and balances.
    function getMaxBuyInputAsset(address token, address assetToken) public view returns (uint256 maxInput) {
        address pairAddr = factory.getPair(token, assetToken);
        IFPair pair = IFPair(pairAddr);
        FERC20 tokenContract = FERC20(token);
        uint256 totalSupply = tokenContract.totalSupply();
        uint256 tokenMaxTx = tokenContract.maxTx();
        uint256 tokenBalance = pair.balance();
        uint256 assetBalance = pair.syntheticAssetBalance();

        return maxBuyInput(totalSupply, tokenMaxTx, tokenBalance, assetBalance);
    }

    function maxBuyInput(
        uint256 totalSupply,
        uint256 tokenMaxTx,
        uint256 tokenBalance,
        uint256 assetBalance
    ) private view returns (uint256 maxBuy) {
        // Max amount of tokens a user can buy (based on maxTx)
        uint256 maxTokenBuy = (totalSupply * tokenMaxTx) / 100;

        // Based on bonding curve formula:
        // amountOut = (amountIn * reserveOut) / (reserveIn + amountIn);
        // maxTokenBuy = (buyAmount * initialSupply) / (launchFee + buyAmount)
        // To solve for buyAmount:
        // maxTokenBuy(launchFee + buyAmount) = buyAmount * initialSupply
        // maxTokenBuy(launchFee) = buyAmount(initialSupply) - maxTokenBuy(buyAmount) = buyAmount(initialSupply - maxTokenBuy)
        // buyAmount = maxTokenBuy(launchFee)/(initialSupply - maxTokenBuy)
        uint256 buyAmount;
        if (tokenBalance <= maxTokenBuy) {
            buyAmount = tokenBalance;
        } else {
            buyAmount = (maxTokenBuy * assetBalance) / (tokenBalance - maxTokenBuy);
        }

        // Account for the tax from the router
        uint256 buyTax = factory.buyTax();
        uint256 buyAmountWithTax = buyAmount * 100 / (100 - buyTax);

        return buyAmountWithTax;
    }
}