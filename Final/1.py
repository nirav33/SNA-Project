import pandas as pd
import networkx as nx
from pyvis.network import Network
from scholarly import scholarly
from itertools import combinations
import os

def extract_scholar_profile(scholar_id):
    """Extract single scholar profile and their coauthors"""
    try:
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author)
        return {
            "name": author.get("name", "N/A"),
            "scholar_id": scholar_id,
            "affiliation": author.get("affiliation", "N/A"),
            "coauthors": author.get("coauthors", [])
        }
    except Exception as e:
        print(f"Error retrieving data for ID {scholar_id}: {e}")
        return None

def create_individual_network(profile):
    """Create network for a single professor"""
    if not profile:
        return None
    
    G = nx.Graph()
    prof_name = profile["name"]
    
    # Add professor as central node
    G.add_node(prof_name, node_type="professor", title=f"{prof_name}<br>Professor<br>Affiliation: {profile['affiliation']}")
    
    # Add coauthors and connections
    for coauthor in profile["coauthors"]:
        coauthor_name = coauthor["name"]
        G.add_node(coauthor_name, node_type="coauthor", title=f"{coauthor_name}<br>Coauthor")
        G.add_edge(prof_name, coauthor_name)
    
    return G

def visualize_individual_network_pyvis(G, professor_name):
    """Visualize network for a single professor using pyvis"""
    if not G:
        return
    
    # Create a pyvis network
    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # Copy the networkx graph to the pyvis network
    for node in G.nodes():
        node_type = G.nodes[node]['node_type']
        title = G.nodes[node].get('title', node)
        
        if node_type == "professor":
            net.add_node(node, label=node, title=title, color="#E41A1C", size=30)
        else:
            net.add_node(node, label=node, title=title, color="#377EB8", size=20)
    
    for edge in G.edges():
        net.add_edge(edge[0], edge[1])
    
    # Set physics layout options
    net.barnes_hut(spring_length=200, spring_strength=0.01, damping=0.09)
    
    # Create output directory if it doesn't exist
    os.makedirs("network_visualizations", exist_ok=True)
    
    # Save the network visualization
    filename = f"network_visualizations/individual_network_{professor_name.replace(' ', '_')}.html"
    net.save_graph(filename)
    print(f"Network visualization saved to {filename}")
    
    return net

def find_shared_connections(profiles):
    """Create network showing connections shared between professors"""
    G = nx.Graph()
    
    # Dictionary to store each professor's coauthors
    prof_coauthors = {}
    
    # Collect all coauthors for each professor
    for profile in profiles:
        if profile:
            prof_name = profile["name"]
            affiliation = profile["affiliation"]
            coauthors = set(coauthor["name"] for coauthor in profile["coauthors"])
            prof_coauthors[prof_name] = coauthors
            
            # Add professor node with affiliation info
            G.add_node(prof_name, node_type="professor", title=f"{prof_name}<br>Professor<br>Affiliation: {affiliation}")
    
    # Find shared connections between professors
    for (prof1, coauthors1), (prof2, coauthors2) in combinations(prof_coauthors.items(), 2):
        shared = coauthors1.intersection(coauthors2)
        if shared:
            # Add edge between professors with shared connections
            G.add_edge(prof1, prof2, weight=len(shared), shared_coauthors=list(shared))
            
            # Add shared coauthor nodes and their connections
            for coauthor in shared:
                G.add_node(coauthor, node_type="shared_coauthor", title=f"{coauthor}<br>Shared Coauthor")
                G.add_edge(prof1, coauthor)
                G.add_edge(prof2, coauthor)
    
    return G

def visualize_shared_network_pyvis(G):
    """Visualize network of shared connections using pyvis"""
    if not G or G.number_of_edges() == 0:
        print("No shared connections found between professors")
        return
    
    # Create a pyvis network
    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # Copy the networkx graph to the pyvis network
    for node in G.nodes():
        node_type = G.nodes[node]['node_type']
        title = G.nodes[node].get('title', node)
        
        if node_type == "professor":
            net.add_node(node, label=node, title=title, color="#E41A1C", size=30)
        elif node_type == "shared_coauthor":
            net.add_node(node, label=node, title=title, color="#4DAF4A", size=20)
    
    for edge in G.edges():
        # If edge is between two professors, use the weight (number of shared coauthors)
        if G.nodes[edge[0]]['node_type'] == "professor" and G.nodes[edge[1]]['node_type'] == "professor":
            weight = G[edge[0]][edge[1]].get('weight', 1)
            net.add_edge(edge[0], edge[1], value=weight, title=f"Shared coauthors: {weight}")
        else:
            net.add_edge(edge[0], edge[1])
    
    # Set physics layout options
    net.barnes_hut(spring_length=250, spring_strength=0.01, damping=0.09)
    
    # Create output directory if it doesn't exist
    os.makedirs("network_visualizations", exist_ok=True)
    
    # Save the network visualization
    filename = "network_visualizations/shared_connections_network.html"
    net.save_graph(filename)
    print(f"Shared connections visualization saved to {filename}")
    
    return net

def print_shared_connections(G):
    """Print details of shared connections between professors"""
    print("\nShared Connections Analysis:")
    shared_data = []
    
    for (prof1, prof2) in G.edges():
        if G.nodes[prof1]['node_type'] == "professor" and G.nodes[prof2]['node_type'] == "professor":
            shared = G[prof1][prof2]['shared_coauthors']
            print(f"\n{prof1} and {prof2} share {len(shared)} coauthor(s):")
            for coauthor in shared:
                print(f"  - {coauthor}")
                shared_data.append({
                    "Professor 1": prof1,
                    "Professor 2": prof2,
                    "Shared Coauthor": coauthor
                })
    
    # Create a DataFrame for easier analysis
    if shared_data:
        df = pd.DataFrame(shared_data)
        
        # Create output directory if it doesn't exist
        os.makedirs("network_visualizations", exist_ok=True)
        
        # Save to CSV
        df.to_csv("network_visualizations/shared_coauthors.csv", index=False)
        print("Shared coauthor data saved to network_visualizations/shared_coauthors.csv")

def analyze_network_statistics(G, professor_name):
    """Analyze network statistics for centrality and connectivity and save to CSV"""
    degree_centrality = nx.degree_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    
    try:
        eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000, tol=1e-6)
    except:
        # Handle case where eigenvector centrality may not converge
        print(f"Warning: Eigenvector centrality calculation didn't converge for {professor_name}'s network")
        eigenvector_centrality = {node: 0 for node in G.nodes()}

    # Print summary statistics for the professor
    print(f"\nStatistical Measures for {professor_name}")
    print(f"Degree Centrality: {degree_centrality[professor_name]:.3f}")
    print(f"Closeness Centrality: {closeness_centrality[professor_name]:.3f}")
    print(f"Betweenness Centrality: {betweenness_centrality[professor_name]:.3f}")
    print(f"Eigenvector Centrality: {eigenvector_centrality[professor_name]:.3f}")
    
    # Create a DataFrame for all nodes
    stats_data = []
    for node in G.nodes():
        stats_data.append({
            'Node': node,
            'Node Type': G.nodes[node]['node_type'],
            'Degree Centrality': degree_centrality[node],
            'Closeness Centrality': closeness_centrality[node],
            'Betweenness Centrality': betweenness_centrality[node],
            'Eigenvector Centrality': eigenvector_centrality[node]
        })
    
    stats_df = pd.DataFrame(stats_data)
    
    # Create output directory if it doesn't exist
    os.makedirs("network_visualizations", exist_ok=True)
    
    # Save to CSV
    stats_df.to_csv(f"network_visualizations/statistics_{professor_name.replace(' ', '_')}.csv", index=False)
    print(f"Network statistics saved to network_visualizations/statistics_{professor_name.replace(' ', '_')}.csv")
    
    # Create an interactive visualization with node sizes based on centrality
    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
    
    for node in G.nodes():
        node_type = G.nodes[node]['node_type']
        title = f"{node}<br>Degree: {degree_centrality[node]:.3f}<br>Closeness: {closeness_centrality[node]:.3f}<br>Betweenness: {betweenness_centrality[node]:.3f}<br>Eigenvector: {eigenvector_centrality[node]:.3f}"
        
        # Size based on degree centrality (scaled)
        size = 20 + degree_centrality[node] * 50
        
        if node_type == "professor":
            net.add_node(node, label=node, title=title, color="#E41A1C", size=30)
        else:
            net.add_node(node, label=node, title=title, color="#377EB8", size=size)
    
    for edge in G.edges():
        net.add_edge(edge[0], edge[1])
    
    # Set physics layout options
    net.barnes_hut(spring_length=200, spring_strength=0.01, damping=0.09)
    
    # Save the centrality visualization
    filename = f"network_visualizations/centrality_{professor_name.replace(' ', '_')}.html"
    net.save_graph(filename)
    print(f"Centrality visualization saved to {filename}")

def main():
    # List of Google Scholar IDs (Replace with actual IDs)
    scholar_ids = ["1Yl1h_YAAAAJ", "UBXqggoAAAAJ", "bmQ917cAAAAJ", "W4lc9bUAAAAJ", "OGQm6cwAAAAJ"]
    
    # Extract all profiles
    print("Extracting scholar profiles...")
    profiles = [extract_scholar_profile(scholar_id) for scholar_id in scholar_ids]
    
    # Generate and save individual networks
    print("\nGenerating individual networks...")
    for profile in profiles:
        if profile:
            G = create_individual_network(profile)
            visualize_individual_network_pyvis(G, profile["name"])
            analyze_network_statistics(G, profile["name"])
            print(f"Created network for {profile['name']}")
    
    # Generate and save shared connections network
    print("\nAnalyzing shared connections...")
    shared_G = find_shared_connections(profiles)
    visualize_shared_network_pyvis(shared_G)
    print_shared_connections(shared_G)
    
    print("\nAll network visualizations have been saved to the 'network_visualizations' directory.")
    print("Open the HTML files in a web browser to explore the interactive network visualizations.")

if __name__ == "__main__":
    main()