from coppeliasim_zmqremoteapi_client import RemoteAPIClient

def connect_to_sim():
    """Establishes connection and enables synchronous mode."""
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    
    # client.setStepping(True)
    
    return client, sim
