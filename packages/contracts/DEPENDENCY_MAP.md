# COMPLETE DEPENDENCY MAP: Prediction Market System with Agent Token Launches

## EXECUTIVE SUMMARY

This document maps all dependencies for deploying a prediction market system that integrates:
1. **Market.sol** - Prediction market core logic with Uniswap V4 integration
2. **BondingV2.sol** - Agent token launch via bonding curve
3. **AgentToken/AgentFactory** - Virtual persona token creation and management
4. **Tax system** - Automated tax collection and management

---

## PHASE 0: EXTERNAL DEPENDENCIES (Already Deployed)

### Uniswap V4 Core Infrastructure
- **IPoolManager** (from @uniswap/v4-core)
  - Status: REAL (must be mainnet PoolManager)
  - Used by: Market.sol (for pool state management)
  - No constructor dependencies - immutable reference

### Uniswap V4 Periphery
- **PositionManager** (from @uniswap/v4-periphery)
  - Status: REAL
  - Constructor param in Market.sol: `_positionManager`
  - Handles liquidity management for YES/NO token pools

### Uniswap Universal Router
- **UniversalRouter** (from @uniswap/universal-router)
  - Status: REAL
  - Constructor param in Market.sol: `_router` (payable)
  - Used for swap operations

### Uniswap Permit2
- **IPermit2** (from @uniswap/permit2)
  - Status: REAL
  - Constructor param in Market.sol: `_permit2`
  - Handles token approvals

### Uniswap V2 Compatibility
- **IUniswapV2Factory** (from protocol-contracts)
  - Status: REAL
  - Used by: AgentTokenV2 for LP pair creation
  - No direct injection - obtained via router

- **IUniswapV2Router02** (from protocol-contracts)
  - Status: REAL
  - Used by: AgentTokenV2 for swaps
  - Injected during initialization

---

## PHASE 1: CORE PREDICTION MARKET CONTRACTS

### 1. Market.sol (PRIMARY ENTRY POINT)

**Role:** Prediction market core with Uniswap V4 integration

**Constructor Parameters:**
```solidity
constructor(
    address admin,              // Market owner/admin
    address _positionManager,   // Uniswap V4 PositionManager
    address payable _router,    // Uniswap UniversalRouter
    address _permit2,          // Uniswap Permit2
    address _swapHook          // MarketUtilsSwapHook instance
)
```

**Internal Dependencies Created:**
- `Id` contract (new instance created in constructor)

**External Dependencies Required:**
- PositionManager (immutable)
- UniversalRouter (immutable)
- Permit2 (immutable)
- MarketUtilsSwapHook (immutable, must be initialized with Market address)
- IPoolManager (for state queries)

**State Requirements:**
- Must call `hook.initialize(address(this))` after deployment

**Mock Capability:** NO - Must be real (interacts with live Uniswap V4)

**Deployment Order:** 2 (after MarketUtilsSwapHook)

---

### 2. MarketUtilsSwapHook.sol

**Role:** Uniswap V4 hook for validating swaps and calculating TWAP prices

**Constructor Parameters:**
```solidity
constructor(
    IPoolManager pm,    // PoolManager instance
    address _owner      // Hook owner
)
```

**Initialization Method:**
```solidity
function initialize(address _market) external
```

**External Dependencies:**
- PoolManager (immutable)

**State Requirements:**
- Must be initialized with Market address via `initialize()` call
- Must be deployed BEFORE Market.sol
- Market must call `hook.initialize(address(this))`

**Mock Capability:** NO - Must be real (Uniswap V4 hook)

**Deployment Order:** 1 (before Market)

---

### 3. Id.sol

**Role:** Simple ID generator for market/proposal tracking

**Constructor Parameters:** None

**Dependencies:** None

**Mock Capability:** YES - Can be mocked or use real

**Deployment Order:** 1a (created automatically by Market)

**Note:** Auto-created inside Market constructor, no manual deployment needed

---

### 4. BasicMarketResolver.sol

**Role:** Verifies market resolution outcomes via signed proofs

**Constructor Parameters:**
```solidity
constructor(
    address systemAdmin,    // System admin (owner)
    address accountHolder   // Account holder role for verification
)
```

**Dependencies:** None (only uses OpenZeppelin)

**Mock Capability:** YES - Can be mocked with dummy verification logic

**Deployment Order:** 1 (independent)

**Can Override:** Implement custom resolver by extending IMarketResolver

---

## PHASE 2: TOKEN CONTRACTS

### 5. DecisionToken (YES/NO Tokens)

**Role:** ERC20 tokens representing YES/NO predictions

**Created:** Dynamically in Market.createProposal()

**Constructor Parameters:**
```solidity
constructor(
    TokenType _tokenType,   // YES or NO
    address minter          // Market.sol address (minter role)
)
```

**Dependencies:** ERC20, ERC20Burnable (OpenZeppelin)

**Mock Capability:** YES - Use mock ERC20

**Deployment Order:** DYNAMIC (created per proposal)

---

### 6. VUSD (Virtual USDC)

**Role:** ERC20 for prediction market liquidity

**Created:** Dynamically in Market.createProposal()

**Constructor Parameters:**
```solidity
constructor(
    address minter  // Market.sol address
)
```

**Dependencies:** ERC20, ERC20Burnable (OpenZeppelin)

**Mock Capability:** YES - Use mock ERC20

**Deployment Order:** DYNAMIC (created per proposal)

---

## PHASE 3: BONDING CURVE & TOKEN LAUNCH SYSTEM

### 7. BondingV2.sol (UPGRADEABLE)

**Role:** Bonding curve for agent token launches with graduation mechanics

**Initialization Parameters:**
```solidity
function initialize(
    address factory_,           // FFactoryV2
    address router_,            // FRouterV2
    address feeTo_,             // Fee recipient
    uint256 fee_,               // Fee amount
    uint256 initialSupply_,     // Initial token supply
    uint256 assetRate_,         // Rate for bonding math (K calculation)
    uint256 maxTx_,             // Max transaction size
    address agentFactory_,      // IAgentFactoryV6 instance
    uint256 gradThreshold_,     // Graduation threshold
    uint256 startTimeDelay_     // Minimum delay before trading starts
) external initializer
```

**Key Requirements:**
- Must be deployed as UUPS proxy
- FFactoryV2 must grant it CREATOR_ROLE
- FRouterV2 must grant it EXECUTOR_ROLE
- Calls to agentFactory require WITHDRAW_ROLE or sender is proposer

**External Dependencies:**
- FFactoryV2 (provides pair creation)
- FRouterV2 (provides buy/sell/graduate logic)
- IAgentFactoryV6 (creates new agent tokens)
- Asset token (used for bonding curve)

**Mock Capability:** NO - Linked to live factories and agent system

**Deployment Order:** 7 (after FFactoryV2, FRouterV2, and AgentFactory)

**DeployParams Structure:**
```solidity
struct DeployParams {
    bytes32 tbaSalt,
    address tbaImplementation,
    uint32 daoVotingPeriod,
    uint256 daoThreshold
}
```
Must be set via `setDeployParams()` before calling `preLaunch()`

---

### 8. FFactoryV2.sol (UPGRADEABLE)

**Role:** Bonding pair factory for agent token launches

**Initialization Parameters:**
```solidity
function initialize(
    address taxVault_,                      // Tax vault address
    uint256 buyTax_,                        // Buy tax percentage
    uint256 sellTax_,                       // Sell tax percentage
    uint256 antiSniperBuyTaxStartValue_,   // Anti-sniper tax start (basis points)
    address antiSniperTaxVault_            // Anti-sniper tax recipient
) external initializer
```

**Key Requirements:**
- Must be deployed as UUPS proxy
- Must call `setRouter()` with FRouterV2 address
- Must grant BondingV2 the CREATOR_ROLE

**External Dependencies:**
- FRouterV2 (set via setRouter)

**Mock Capability:** PARTIAL - Can mock for testing but must track real pairs

**Deployment Order:** 4 (before FRouterV2 and BondingV2)

---

### 9. FRouterV2.sol (UPGRADEABLE)

**Role:** Router for bonding curve swaps and graduations

**Initialization Parameters:**
```solidity
function initialize(
    address factory_,       // FFactoryV2
    address assetToken_     // Asset token for trading
) external initializer
```

**Key Requirements:**
- Factory must have already initialized
- Factory must call setRouter(address(this)) in FRouterV2

**External Dependencies:**
- FFactoryV2
- Asset token (IERC20)
- Tax manager contracts (optional)

**Mock Capability:** PARTIAL - Can mock pair interactions

**Deployment Order:** 5 (after FFactoryV2, before BondingV2)

**Tax Manager Integration:**
```solidity
function setTaxManager(address newManager) public onlyRole(ADMIN_ROLE)
function setAntiSniperTaxManager(address newManager) public onlyRole(ADMIN_ROLE)
```

---

### 10. FPairV2.sol

**Role:** Individual bonding curve pair for token/asset trading

**Constructor Parameters:**
```solidity
constructor(
    address router_,
    address token0,         // Agent token
    address token1,         // Asset token
    uint256 startTime_,     // Trading start time
    uint256 startTimeDelay_ // Minimum delay requirement
)
```

**Dependencies:**
- Router (FRouterV2)

**Created:** Dynamically by FFactoryV2.createPair()

**Mock Capability:** YES - Can mock with fixed reserves

**Deployment Order:** DYNAMIC (created per token)

---

## PHASE 4: AGENT FACTORY & TOKEN SYSTEM

### 11. AgentFactoryV2 (PROTOCOL-CONTRACTS, UPGRADEABLE)

**Role:** Creates agent personas with tokens, DAOs, NFTs, and TBAs

**Initialization Parameters:**
```solidity
function initialize(
    address tokenImplementation_,    // AgentTokenV2 clone template
    address veTokenImplementation_,  // VeToken clone template
    address daoImplementation_,      // DAO clone template
    address tbaRegistry_,            // ERC6551 registry
    address assetToken_,             // Base currency (e.g., $VIRTUAL)
    address nft_,                    // AgentNFT instance
    uint256 applicationThreshold_,   // Min asset for application
    address vault_                   // NFT vault
) public initializer
```

**Key Setter Methods (Must be called):**
```solidity
setTokenAdmin(address)              // Required for token creation
setUniswapRouter(address)           // UniswapV2Router02
setTokenSupplyParams(...)           // Token supply config
setTokenTaxParams(...)              // Tax config
setAssetToken(address)              // Asset token address
```

**Internal Cloning:**
- Creates AgentTokenV2 instances via proxy clone
- Creates AgentVeToken instances via proxy clone
- Creates DAO instances via proxy clone

**External Dependencies:**
- AgentTokenV2 (implementation)
- AgentVeToken (implementation)
- AgentDAO (implementation)
- AgentNFT
- ERC6551Registry
- Asset token

**Mock Capability:** PARTIAL - Can mock for testing

**Deployment Order:** 8 (after implementations are deployed)

**Interacts with BondingV2:**
- `createNewAgentTokenAndApplication()` - Called by BondingV2.preLaunch()
- `updateApplicationThresholdWithApplicationId()` - Called by BondingV2._openTradingOnUniswap()
- `executeBondingCurveApplicationSalt()` - Called by BondingV2._openTradingOnUniswap()
- `addBlacklistAddress()` / `removeBlacklistAddress()` - Called during graduation

---

### 12. AgentTokenV2 (PROTOCOL-CONTRACTS, UPGRADEABLE)

**Role:** Individual agent token with tax system and liquidity pools

**Initialization Parameters:**
```solidity
function initialize(
    address[3] memory integrationAddresses_,  // [owner, router, pairToken]
    bytes memory baseParams_,                 // abi.encode(name, symbol)
    bytes memory supplyParams_,               // Supply configuration
    bytes memory taxParams_                   // Tax configuration
) external initializer
```

**Supply Parameters Structure:**
```solidity
struct ERC20SupplyParameters {
    uint256 maxSupply,
    uint256 lpSupply,
    uint256 vaultSupply,
    uint256 maxTokensPerWallet,
    uint256 maxTokensPerTxn,
    uint256 botProtectionDurationInSeconds,
    address vault
}
```

**Tax Parameters Structure:**
```solidity
struct ERC20TaxParameters {
    uint256 projectBuyTaxBasisPoints,
    uint256 projectSellTaxBasisPoints,
    uint256 taxSwapThresholdBasisPoints,
    address projectTaxRecipient
}
```

**Created:** Via AgentFactory.executeApplication()

**External Dependencies:**
- UniswapV2Router02
- Pair token (asset)
- Liquidity pools (auto-created)

**Mock Capability:** YES - Can mock with simple ERC20

**Deployment Order:** DYNAMIC (cloned per agent)

---

## PHASE 5: TAX SYSTEM

### 13. BondingTax.sol (UPGRADEABLE, OPTIONAL)

**Role:** Collects and swaps bonding curve taxes for assets

**Initialization Parameters:**
```solidity
function initialize(
    address defaultAdmin_,
    address assetToken_,
    address taxToken_,
    address router_,
    address bondingRouter_,
    address treasury_,
    uint256 minSwapThreshold_,
    uint256 maxSwapThreshold_
) external initializer
```

**Key Methods:**
```solidity
swapForAsset() external onlyBondingRouter returns (bool, uint256)
```

**Called By:** FRouterV2 during buy/sell operations

**External Dependencies:**
- Asset token (IERC20)
- Tax token (IERC20)
- UniswapV2Router (IRouter)
- Treasury address

**Mock Capability:** YES - Can mock

**Deployment Order:** 6 (if using tax system)

**Note:** Linked to FRouterV2 and BondingV2

---

## PHASE 6: MARKET TOKENS (OPTIONAL)

### 14. MockStablecoin.sol

**Role:** Test stablecoin for prediction markets

**Constructor Parameters:**
```solidity
constructor(
    string memory name,
    string memory symbol,
    uint8 decimalsValue,
    address initialOwner
)
```

**Dependencies:** ERC20, Ownable

**Mock Capability:** YES - Is a mock

**Deployment Order:** 1 (independent, for testing)

**Can use:** Real stablecoin (USDC, USDT, etc.) in production

---

### 15. MockAID.sol

**Role:** Mock agent token for testing

**Constructor Parameters:**
```solidity
constructor()
```

**Dependencies:** ERC20, Ownable

**Mock Capability:** YES - Is a mock

**Deployment Order:** 1 (independent, for testing)

---

## COMPLETE DEPLOYMENT SEQUENCE

### Step 0: Deploy External Dependencies (if needed for testing)
1. Deploy PoolManager (or use existing)
2. Deploy PositionManager (or use existing)
3. Deploy UniversalRouter (or use existing)
4. Deploy Permit2 (or use existing)

### Step 1: Deploy Test Tokens (Optional)
1. MockStablecoin (as asset token)
2. MockAID (as market token)

### Step 2: Deploy Market System
1. **MarketUtilsSwapHook**
   - Constructor: PoolManager, owner
   
2. **Market**
   - Constructor: admin, PositionManager, UniversalRouter, Permit2, SwapHook
   - Call: hook.initialize(Market.address)

3. **BasicMarketResolver**
   - Constructor: systemAdmin, accountHolder

### Step 3: Deploy Bonding Factory System
1. **FFactoryV2** (proxy)
   - Initialize: taxVault, buyTax, sellTax, antiSniperTax, antiSniperVault
   
2. **FRouterV2** (proxy)
   - Initialize: FFactoryV2, assetToken
   - Call: FFactoryV2.setRouter(FRouterV2.address)
   - Call: FRouterV2.setTaxManager() [optional]

3. **BondingTax** (proxy, optional)
   - Initialize: admin, assetToken, taxToken, router, bondingRouter, treasury, min, max
   - Call: FRouterV2.setTaxManager(BondingTax.address)

### Step 4: Deploy Agent System
1. **AgentTokenV2** (implementation)
   - Constructor: (inherited, disable initializers)

2. **AgentVeToken** (implementation)
   - Constructor: (inherited, disable initializers)

3. **AgentDAO** (implementation)
   - Constructor: (inherited, disable initializers)

4. **AgentNFT**
   - Constructor: (depends on implementation)

5. **AgentFactoryV2** (proxy)
   - Initialize: tokenImpl, veImpl, daoImpl, registry, assetToken, nft, threshold, vault
   - Call: setTokenAdmin(address)
   - Call: setUniswapRouter(UniswapV2Router)
   - Call: setTokenSupplyParams(maxSupply, lpSupply, vaultSupply, maxWallet, maxTx, botDuration, vault)
   - Call: setTokenTaxParams(buyTax, sellTax, swapThreshold, taxRecipient)

### Step 5: Deploy BondingV2
1. **BondingV2** (proxy)
   - Initialize: factory, router, feeTo, fee, supply, assetRate, maxTx, agentFactory, threshold, startDelay
   - Call: FFactoryV2.grantRole(CREATOR_ROLE, BondingV2.address)
   - Call: FRouterV2.grantRole(EXECUTOR_ROLE, BondingV2.address)
   - Call: BondingV2.setDeployParams(tbaSalt, tbaImpl, daoVotingPeriod, daoThreshold)
   - Call: BondingV2.setLaunchParams(startDelay, teamReserved, teamWallet)

---

## DEPENDENCY MATRIX

```
LEGEND: ▶ depends on, ◀ depended by, ◆ can mock

┌─ Market.sol (Core Market)
│  ▶ MarketUtilsSwapHook
│  ▶ PoolManager (real)
│  ▶ PositionManager (real)
│  ▶ UniversalRouter (real)
│  ▶ Permit2 (real)
│  ▶ Id (internal creation)
│  ◀ BasicMarketResolver (optional)
│
├─ MarketUtilsSwapHook
│  ▶ PoolManager (real)
│  ◀ Market
│
├─ BasicMarketResolver
│  (no dependencies)
│  ◀ Market (calls verifyResolution)
│
├─ FFactoryV2
│  ▶ FRouterV2 (set via setRouter)
│  ◀ BondingV2
│  ◀ FPairV2 (created by factory)
│
├─ FRouterV2
│  ▶ FFactoryV2
│  ▶ Asset token (IERC20)
│  ▶ BondingTax (optional)
│  ◀ BondingV2
│  ◀ FPairV2 (calls router methods)
│
├─ FPairV2
│  ▶ FRouterV2
│  ◀ FFactoryV2 (creates)
│
├─ BondingV2
│  ▶ FFactoryV2
│  ▶ FRouterV2
│  ▶ IAgentFactoryV6 (AgentFactoryV2)
│  ▶ Asset token (IERC20)
│  ◆ Can mock agent factory for testing
│
├─ AgentFactoryV2
│  ▶ AgentTokenV2 (implementation/clone)
│  ▶ AgentVeToken (implementation/clone)
│  ▶ AgentDAO (implementation/clone)
│  ▶ AgentNFT
│  ▶ ERC6551Registry
│  ▶ Asset token
│  ◀ BondingV2 (calls createNewAgentToken)
│
├─ AgentTokenV2
│  ▶ UniswapV2Router02 (real)
│  ▶ Pair token (asset)
│  ◀ AgentFactoryV2 (clones)
│
├─ BondingTax (optional)
│  ▶ Asset token
│  ▶ Tax token
│  ▶ UniswapV2Router (IRouter)
│  ◀ FRouterV2
│
└─ Test Tokens (Mock)
   ├─ MockStablecoin ◆
   └─ MockAID ◆
```

---

## DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Decide on asset token (USDC, mock, etc.)
- [ ] Determine tax rates and thresholds
- [ ] Set up vault address for NFTs
- [ ] Prepare treasury address for taxes
- [ ] Get TBA registry address
- [ ] Get Uniswap V2 router address
- [ ] Get PoolManager address
- [ ] Get PositionManager address
- [ ] Get UniversalRouter address
- [ ] Get Permit2 address

### Deployment Phase 1: Core Market
- [ ] Deploy MarketUtilsSwapHook
- [ ] Deploy Market
- [ ] Initialize hook with Market address
- [ ] Deploy BasicMarketResolver

### Deployment Phase 2: Bonding System
- [ ] Deploy FFactoryV2 (proxy)
- [ ] Deploy FRouterV2 (proxy)
- [ ] Call FFactoryV2.setRouter()
- [ ] Deploy BondingTax (proxy, if using)
- [ ] Call FRouterV2.setTaxManager() (if using)

### Deployment Phase 3: Agent System
- [ ] Deploy AgentTokenV2 (implementation)
- [ ] Deploy AgentVeToken (implementation)
- [ ] Deploy AgentDAO (implementation)
- [ ] Deploy/Verify AgentNFT
- [ ] Deploy AgentFactoryV2 (proxy)
- [ ] Call AgentFactory.setTokenAdmin()
- [ ] Call AgentFactory.setUniswapRouter()
- [ ] Call AgentFactory.setTokenSupplyParams()
- [ ] Call AgentFactory.setTokenTaxParams()

### Deployment Phase 4: BondingV2
- [ ] Deploy BondingV2 (proxy)
- [ ] Grant FFactoryV2.CREATOR_ROLE to BondingV2
- [ ] Grant FRouterV2.EXECUTOR_ROLE to BondingV2
- [ ] Call BondingV2.setDeployParams()
- [ ] Call BondingV2.setLaunchParams()

### Verification
- [ ] Market can create markets
- [ ] BondingV2 can create agent tokens
- [ ] Tokens can trade on bonding curve
- [ ] Graduation mechanics work
- [ ] Tax system operational
- [ ] Market resolution works

---

## CONSTRUCTOR PARAMETERS REFERENCE

### Quick Reference by Contract

| Contract | Type | Initialization Method | Key Parameters |
|----------|------|----------------------|-----------------|
| MarketUtilsSwapHook | Regular | constructor | PoolManager, owner |
| Market | Regular | constructor | admin, positionManager, router, permit2, hook |
| BasicMarketResolver | Regular | constructor | systemAdmin, accountHolder |
| FFactoryV2 | Proxy | initialize | taxVault, buyTax, sellTax, antiSniperTax, antiSniperVault |
| FRouterV2 | Proxy | initialize | factory, assetToken |
| BondingV2 | Proxy | initialize | factory, router, feeTo, fee, supply, rate, maxTx, agentFactory, threshold, delay |
| AgentFactoryV2 | Proxy | initialize | tokenImpl, veImpl, daoImpl, registry, asset, nft, threshold, vault |
| AgentTokenV2 | Proxy | initialize | [owner, uniRouter, pairToken], baseParams, supplyParams, taxParams |
| BondingTax | Proxy | initialize | admin, asset, taxToken, router, bondingRouter, treasury, minThreshold, maxThreshold |

---

## MOCKING STRATEGY

### Can Be Mocked (Testing Only)
1. **BasicMarketResolver** - Replace with simple resolver
2. **BondingTax** - Replace with tax accumulator
3. **AgentTokenV2** - Use simple ERC20 mock
4. **AgentVeToken** - Use simple VE mock
5. **AgentDAO** - Use simple DAO mock
6. **FPairV2** - Use pair mock with fixed reserves
7. **FRouterV2** - Use router mock (partially)
8. **FFactoryV2** - Use factory mock (partially)

### Must Be Real (Production)
1. **Market.sol** - Core business logic
2. **MarketUtilsSwapHook** - Uniswap V4 hook
3. **BondingV2.sol** - Core token launch logic
4. **AgentFactoryV2** - Creates real clones
5. **PoolManager** - Uniswap V4 core
6. **PositionManager** - Uniswap V4 periphery
7. **UniversalRouter** - Uniswap routing
8. **Permit2** - Token approvals

### Test Configuration (Localhost)
```solidity
// Deploy mocks for:
- PoolManager (or mock)
- PositionManager (or mock)
- UniversalRouter (or mock)
- Permit2 (or mock)
- MockStablecoin (asset)
- MockAID (market token)

// Deploy real implementations for:
- All Market contracts
- All Bonding contracts
- AgentFactory and token system
```

---

## STATE VARIABLES THAT NEED CONFIGURATION

### BondingV2
```solidity
launchParams.startTimeDelay        // Min time before trading starts
launchParams.teamTokenReservedSupply // Reserved for team
launchParams.teamTokenReservedWallet // Team wallet address
_deployParams.tbaSalt              // TBA salt
_deployParams.tbaImplementation     // TBA implementation
_deployParams.daoVotingPeriod       // DAO voting period
_deployParams.daoThreshold          // DAO threshold
```

### AgentFactoryV2
```solidity
assetToken                         // Base currency
tokenImplementation                // AgentTokenV2 impl
veTokenImplementation              // VeToken impl
daoImplementation                  // DAO impl
nft                               // AgentNFT
tbaRegistry                       // ERC6551 registry
_tokenSupplyParams                // Supply config
_tokenTaxParams                   // Tax config
_uniswapRouter                    // UniswapV2Router
_tokenAdmin                       // Token admin address
maturityDuration                  // Staking maturity
```

### FRouterV2
```solidity
factory                           // FFactoryV2
assetToken                        // Asset token
taxManager                        // BondingTax (optional)
antiSniperTaxManager              // Anti-sniper tax (optional)
```

### Market
```solidity
POOL_FEE                         // Uniswap pool fee (3000 = 0.3%)
```

---

## ERROR RECOVERY & FAILURE MODES

### If Market Creation Fails
- Check PoolManager is accessible
- Check PositionManager has proper roles
- Check hook is properly initialized

### If BondingV2 Fails to Launch
- Check agentFactory is configured with WITHDRAW_ROLE
- Check FFactory has CREATOR_ROLE for BondingV2
- Check FRouter has EXECUTOR_ROLE for BondingV2
- Check asset token has sufficient liquidity

### If Token Graduation Fails
- Check agentFactory.executeApplication() requirements
- Check blacklist/whitelist settings
- Check asset balance in bonding pair

### If Market Resolution Fails
- Check resolver is properly deployed
- Check signature verification setup
- Check proof format matches resolver expectations

---

## GAS OPTIMIZATION NOTES

1. **Market creation** - Uses dynamic ERC20 deployment (moderate gas)
2. **BondingV2 initialization** - Upgradeable proxy (one-time)
3. **AgentFactory cloning** - Uses Clones.clone() (optimized)
4. **Tax swaps** - Batched via thresholds (efficient)
5. **V4 pools** - Concentrated liquidity reduces slippage

---

## SECURITY CONSIDERATIONS

1. **Access Control:**
   - BondingV2 requires CREATOR_ROLE on factory
   - AgentFactory requires WITHDRAW_ROLE for execution
   - Market requires admin role for fee changes

2. **Reentrancy:**
   - BondingV2 uses ReentrancyGuard
   - FRouterV2 uses ReentrancyGuard
   - FPairV2 uses ReentrancyGuard

3. **Rate Limiting:**
   - Anti-sniper tax reduces early buying
   - Max transaction limits in agent tokens
   - Bonding curve thresholds prevent abuse

4. **Initialization:**
   - All UUPS proxies disable initializers in constructor
   - Initialize must be called immediately after deployment
   - Set crucial parameters before enabling trading

---

## TESTING DEPLOYMENT FLOW

```solidity
// 1. Deploy all infrastructure
await deployMarketInfra();

// 2. Deploy bonding system
await deployBondingSystem();

// 3. Deploy agent system
await deployAgentSystem();

// 4. Deploy bonding wrapper
await deployBondingV2();

// 5. Test token lifecycle
await testPreLaunch();    // Create token on bonding curve
await testTrading();       // Buy/sell on bonding curve
await testGraduation();    // Graduate to Uniswap
await testMarket();        // Create and resolve market

// 6. Verify all integrations
await verifyIntegrations();
```

