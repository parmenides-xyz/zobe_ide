import requests
import json
import base64
 
def get_latest_inference(topic_id, rpc_url):
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "abci_query",
            "params": {
                "path": "/allora.emissions.v1.Query/GetLatestNetworkInferences",
                "data": bytes(json.dumps({"topic_id": 1}), 'utf-8').hex(),
                "prove": False
            }
        }
        
        response = requests.post(rpc_url, json=payload)
        response.raise_for_status()
        
        result = response.json()["result"]
        if result["response"]["code"] != 0:
            raise Exception(f"Query failed with code {result['response']['code']}")
        
        # Decode the response value
        decoded_value = base64.b64decode(result["response"]["value"]).decode('utf-8')
        parsed_value = json.loads(decoded_value)
        
        return parsed_value
    except Exception as e:
        print(f"Error querying Allora RPC: {e}")
        raise
 
# Example usage
try:
    data = get_latest_inference(1, "https://allora-rpc.testnet.allora.network")
    print(f"Latest inference: {data['network_inferences']['combined_value']}")
    print(f"Confidence intervals: {data['confidence_interval_values']}")
except Exception as e:
    print(f"Failed to get inference: {e}")