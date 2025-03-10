import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from scholarly import scholarly
from itertools import combinations

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
    G.add_node(prof_name, node_type="professor")
    
    # Add coauthors and connections
    for coauthor in profile["coauthors"]:
        coauthor_name = coauthor["name"]
        G.add_node(coauthor_name, node_type="coauthor")
        G.add_edge(prof_name, coauthor_name)
    
    return G

def visualize_individual_network(G, professor_name):
    """Visualize network for a single professor"""
    if not G:
        return
    
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=1)
    
    # Draw nodes with different colors for professor and coauthors
    node_colors = ['red' if G.nodes[node]['node_type'] == "professor" else 'lightblue' 
                  for node in G.nodes()]
    
    nx.draw(G, pos,
            node_color=node_colors,
            node_size=[3000 if G.nodes[node]['node_type'] == "professor" else 1000 
                      for node in G.nodes()],
            with_labels=True,
            font_size=8,
            edge_color='gray',
            alpha=0.7)
    
    plt.title(f"Collaboration Network - {professor_name}")
    plt.savefig(f"individual_network_{professor_name.replace(' ', '_')}.png", 
                bbox_inches='tight')
    plt.close()

def find_shared_connections(profiles):
    """Create network showing connections shared between professors"""
    G = nx.Graph()
    
    # Dictionary to store each professor's coauthors
    prof_coauthors = {}
    
    # Collect all coauthors for each professor
    for profile in profiles:
        if profile:
            prof_name = profile["name"]
            coauthors = set(coauthor["name"] for coauthor in profile["coauthors"])
            prof_coauthors[prof_name] = coauthors
            
            # Add professor node
            G.add_node(prof_name, node_type="professor")
    
    # Find shared connections between professors
    for (prof1, coauthors1), (prof2, coauthors2) in combinations(prof_coauthors.items(), 2):
        shared = coauthors1.intersection(coauthors2)
        if shared:
            # Add edge between professors with shared connections
            G.add_edge(prof1, prof2, weight=len(shared), shared_coauthors=list(shared))
            
            # Add shared coauthor nodes and their connections
            for coauthor in shared:
                G.add_node(coauthor, node_type="shared_coauthor")
                G.add_edge(prof1, coauthor)
                G.add_edge(prof2, coauthor)
    
    return G

def visualize_shared_network(G):
    """Visualize network of shared connections"""
    if not G or G.number_of_edges() == 0:
        print("No shared connections found between professors")
        return
    
    plt.figure(figsize=(15, 10))
    pos = nx.spring_layout(G, k=1)
    
    # Draw nodes with different colors for professors and shared coauthors
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if G.nodes[node]['node_type'] == "professor":
            node_colors.append('red')
            node_sizes.append(3000)
        else:
            node_colors.append('lightgreen')
            node_sizes.append(1000)
    
    # Draw edges with varying thickness based on number of shared connections
    edge_weights = [G[u][v].get('weight', 1) for u, v in G.edges()]
    
    nx.draw(G, pos,
            node_color=node_colors,
            node_size=node_sizes,
            with_labels=True,
            font_size=8,
            width=edge_weights,
            edge_color='gray',
            alpha=0.7)
    
    # Add legend
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                 markerfacecolor=c, label=l, markersize=10)
                      for c, l in [('red', 'Professors'),
                                 ('lightgreen', 'Shared Collaborators')]]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
    
    plt.title("Shared Connections Between Professors")
    plt.savefig("shared_connections_network.png", bbox_inches='tight')
    plt.close()

def print_shared_connections(G):
    """Print details of shared connections between professors"""
    print("\nShared Connections Analysis:")
    for (prof1, prof2) in G.edges():
        if G.nodes[prof1]['node_type'] == "professor" and G.nodes[prof2]['node_type'] == "professor":
            shared = G[prof1][prof2]['shared_coauthors']
            print(f"\n{prof1} and {prof2} share {len(shared)} coauthor(s):")
            for coauthor in shared:
                print(f"  - {coauthor}")
                
def analyze_network_statistics(G, professor_name):
    """Analyze network statistics for centrality and connectivity."""
    degree_centrality = nx.degree_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000, tol=1e-6)

    print(f"\nStatistical Measures for {professor_name}")
    print(f"Degree Centrality: {degree_centrality}")
    print(f"Closeness Centrality: {closeness_centrality}")
    print(f"Betweenness Centrality: {betweenness_centrality}")
    print(f"Eigenvector Centrality: {eigenvector_centrality}")

    # Plotting with adjusted bar width
    plt.figure(figsize=(12, 6))
    x = range(len(degree_centrality))
    
    plt.bar(x, degree_centrality.values(), color='blue', label='Degree Centrality', width=0.2)
    plt.bar(x, closeness_centrality.values(), color='green', label='Closeness Centrality', width=0.2)
    plt.bar(x, betweenness_centrality.values(), color='red', label='Betweenness Centrality', width=0.2)
    plt.bar(x, eigenvector_centrality.values(), color='purple', label='Eigenvector Centrality', width=0.2)
    
    plt.xticks(x, list(degree_centrality.keys()), rotation=45, ha='right')
    plt.legend()
    plt.title(f'Graph-Based Statistical Measures - {professor_name}')
    plt.tight_layout()
    plt.savefig(f"statistics_{professor_name.replace(' ', '_')}.png")
    plt.close()


def main():
    # List of Google Scholar IDs (Replace with actual IDs)
    scholar_ids = ["1Yl1h_YAAAAJ", "UBXqggoAAAAJ", "bmQ917cAAAAJ", "W4lc9bUAAAAJ", "OGQm6cwAAAAJ"]
    
    # Extract all profiles
    profiles = [extract_scholar_profile(scholar_id) for scholar_id in scholar_ids]
    
    # Generate and save individual networks
    # print("Generating individual networks...")
    # for profile in profiles:
    #     if profile:
    #         G = create_individual_network(profile)
    #         visualize_individual_network(G, profile["name"])
    #         print(f"Created network for {profile['name']}")
    
    # # Generate and save shared connections network
    # print("\nAnalyzing shared connections...")
    # shared_G = find_shared_connections(profiles)
    # visualize_shared_network(shared_G)
    # print_shared_connections(shared_G)
    
    for profile in profiles:
        if profile:
            G = create_individual_network(profile)
            visualize_individual_network(G, profile["name"])
            analyze_network_statistics(G, profile["name"])
            print(f"Created network for {profile['name']}")

    # Generate and save shared connections network
    print("\nAnalyzing shared connections...")
    shared_G = find_shared_connections(profiles)
    visualize_shared_network(shared_G)
    print_shared_connections(shared_G)


if __name__ == "__main__":
    main()