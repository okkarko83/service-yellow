# service-yellow/app.py
import os
import requests
from flask import Flask, render_template

app = Flask(__name__)

def get_peer_services():
    """
    Parses peer services from the PEER_SERVICES environment variable.
    The variable should be a comma-separated string of name:url pairs.
    Example: "blue:http://service-blue:5000,green:http://service-green:5001"
    """
    peers = {}
    peer_env = os.getenv('PEER_SERVICES')
    
    if not peer_env:
        # Fallback to a default if the environment variable is not set
        print("Warning: PEER_SERVICES environment variable not set. Using default peers.")
        return {
            "blue": "http://service-blue:5000",
            "green": "http://service-green:5001",
        }
    
    try:
        for peer in peer_env.split(','):
            # Split only on the first colon to handle URLs with colons
            name, url = peer.split(':', 1)
            peers[name.strip()] = url.strip()
        return peers
    except ValueError:
        print(f"Warning: Malformed PEER_SERVICES environment variable: '{peer_env}'. Using empty peer list.")
        return {}

PEER_SERVICES = get_peer_services()

def get_version():
    """Reads the version from the version.txt file."""
    try:
        with open("version.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "N/A"

def get_peer_status(service_name, service_url):
    """Checks the health of a peer service and gets its version."""
    try:
        response = requests.get(f"{service_url}/health", timeout=1)
        if response.status_code == 200:
            data = response.json()
            return "up", data.get("version", "N/A")
        return "down", "N/A"
    except requests.exceptions.RequestException:
        return "down", "N/A"

@app.route('/')
def home():
    """Renders the home page with the status of self and peer services."""
    my_version = get_version()
    peer_statuses = {}
    for name, url in PEER_SERVICES.items():
        status, version = get_peer_status(name, url)
        peer_statuses[name] = {"status": status, "version": version}

    return render_template(
        'index.html',
        service_name='Yellow',
        version=my_version,
        peers=peer_statuses
    )

@app.route('/health')
def health_check():
    """Provides a health check endpoint."""
    return {"status": "up", "version": get_version()}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
