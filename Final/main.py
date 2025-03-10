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
    G.add_node(prof_name, title=f"{prof_name}\n{profile['affiliation']}", 
               group="professor", size=25)
    
    # Add coauthors and connections
    for coauthor in profile["coauthors"]:
        coauthor_name = coauthor["name"]
        G.add_node(coauthor_name, title=coauthor_name, group="coauthor", size=15)
        G.add_edge(prof_name, coauthor_name)
    
    return G

def visualize_individual_network(G, professor_name):
    """Visualize network for a single professor using pyvis"""
    if not G:
        return
    
    # Create pyvis network
    net = Network(height="750px", width="100%", notebook=False, directed=False, bgcolor="#ffffff")
    
    # Set physics layout options
    net.barnes_hut(spring_length=200, spring_strength=0.05, damping=0.09)
    
    # Add nodes from networkx graph
    for node, attrs in G.nodes(data=True):
        net.add_node(node, label=node, title=attrs.get('title', node), 
                     group=attrs.get('group', 'default'), size=attrs.get('size', 15))
    
    # Add edges from networkx graph
    for source, target in G.edges():
        net.add_edge(source, target)
    
    # Generate interactive HTML file
    filename = f"individual_network_{professor_name.replace(' ', '_')}.html"
    net.save_graph(filename)
    print(f"Created interactive network for {professor_name} saved as {filename}")
    
    return filename

def create_combined_network(profiles):
    """Create a combined network of all professors and their coauthors"""
    G = nx.Graph()
    
    # Process each professor profile
    for profile in profiles:
        if profile:
            prof_name = profile["name"]
            # Add professor node
            G.add_node(prof_name, title=f"{prof_name}\n{profile['affiliation']}", 
                       group="professor", size=25)
            
            # Add coauthor nodes and connections
            for coauthor in profile["coauthors"]:
                coauthor_name = coauthor["name"]
                # Check if this is a new coauthor
                if not G.has_node(coauthor_name):
                    G.add_node(coauthor_name, title=coauthor_name, group="coauthor", size=15)
                G.add_edge(prof_name, coauthor_name)
    
    # Find shared coauthors and update their attributes
    coauthor_connections = {}
    for node in G.nodes():
        if G.nodes[node].get('group') == 'coauthor':
            connections = list(G.neighbors(node))
            professors = [n for n in connections if G.nodes[n].get('group') == 'professor']
            if len(professors) > 1:  # If connected to multiple professors
                G.nodes[node]['group'] = 'shared_coauthor'
                G.nodes[node]['size'] = 20
                G.nodes[node]['title'] = f"{node}\nShared by: {', '.join(professors)}"
                
                # Add direct connections between professors who share this coauthor
                for prof1, prof2 in combinations(professors, 2):
                    if G.has_edge(prof1, prof2):
                        # Increase weight if edge exists
                        G[prof1][prof2]['weight'] = G[prof1][prof2].get('weight', 1) + 1
                        # Update shared coauthors list
                        if 'shared_coauthors' in G[prof1][prof2]:
                            G[prof1][prof2]['shared_coauthors'].append(node)
                        else:
                            G[prof1][prof2]['shared_coauthors'] = [node]
                    else:
                        # Create new edge
                        G.add_edge(prof1, prof2, weight=1, shared_coauthors=[node])
    
    return G

def visualize_combined_network(G):
    """Visualize the combined network using pyvis"""
    if not G:
        return
    
    # Create pyvis network
    net = Network(height="800px", width="100%", notebook=False, directed=False, bgcolor="#ffffff")
    
    # Configure physics for better visualization
    net.barnes_hut(spring_length=200, spring_strength=0.05, damping=0.09, gravity=-80000)
    
    # Set node colors by group
    color_map = {
        "professor": "#e41a1c",          # Red
        "coauthor": "#377eb8",           # Blue
        "shared_coauthor": "#4daf4a"     # Green
    }
    
    # Add nodes from networkx graph
    for node, attrs in G.nodes(data=True):
        group = attrs.get('group', 'default')
        color = color_map.get(group, "#cccccc")
        net.add_node(node, label=node, title=attrs.get('title', node), 
                     group=group, size=attrs.get('size', 15), color=color)
    
    # Add edges from networkx graph with varying widths based on weight
    for source, target, attrs in G.edges(data=True):
        weight = attrs.get('weight', 1)
        # Make professor-professor connections thicker and highlighted
        if (G.nodes[source].get('group') == 'professor' and 
            G.nodes[target].get('group') == 'professor'):
            width = weight * 3
            title = f"Shared coauthors: {', '.join(attrs.get('shared_coauthors', []))}"
            color = "#ff9900"  # Orange for professor-professor connections
        else:
            width = 1
            title = ""
            color = "#999999"  # Grey for other connections
            
        net.add_edge(source, target, width=width, title=title, color=color)
    
    # Add legend as HTML
    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "size": 12
        }
      },
      "edges": {
        "color": {
          "inherit": false
        },
        "smooth": {
          "enabled": false
        }
      },
      "physics": {
        "forceAtlas2Based": {
          "springLength": 100
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      }
    }
    """)
    
    # Save the network visualization
    filename = "combined_network.html"
    net.save_graph(filename)
    print(f"Created combined network visualization saved as {filename}")
    
    return filename

def print_shared_connections(G):
    """Print details of shared connections between professors"""
    print("\nShared Connections Analysis:")
    for (prof1, prof2, attrs) in G.edges(data=True):
        if (G.nodes[prof1].get('group') == "professor" and 
            G.nodes[prof2].get('group') == "professor"):
            if 'shared_coauthors' in attrs:
                shared = attrs['shared_coauthors']
                print(f"\n{prof1} and {prof2} share {len(shared)} coauthor(s):")
                for coauthor in shared:
                    print(f"  - {coauthor}")

def create_integrated_visualization(profiles):
    """Create an HTML file integrating all networks with tabs for navigation"""
    individual_htmls = []
    combined_html = ""
    
    # First create all individual networks and the combined network
    for profile in profiles:
        if profile:
            G = create_individual_network(profile)
            filename = visualize_individual_network(G, profile["name"])
            individual_htmls.append((profile["name"], filename))
    
    combined_G = create_combined_network(profiles)
    combined_html = visualize_combined_network(combined_G)
    print_shared_connections(combined_G)
    
    # Create an index.html file with links to all visualizations
    with open("index.html", "w") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Academic Collaboration Networks</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .nav { margin-bottom: 20px; }
                .nav a { 
                    padding: 10px 15px; 
                    background-color: #f0f0f0; 
                    margin-right: 5px; 
                    text-decoration: none;
                    color: #333;
                    border-radius: 5px;
                }
                .nav a:hover { background-color: #ddd; }
                .nav a.active { background-color: #4CAF50; color: white; }
                h1 { color: #2c3e50; }
                p { line-height: 1.6; }
            </style>
        </head>
        <body>
            <h1>Academic Collaboration Network Analysis</h1>
            <p>This visualization shows collaboration networks between academics based on Google Scholar profiles.</p>
            
            <div class="nav">
                <a href="combined_network.html" target="_blank">Combined Network</a>
        """)
        
        for name, html_file in individual_htmls:
            f.write(f'<a href="{html_file}" target="_blank">{name}</a>\n')
        
        f.write("""
            </div>
            
            <h2>How to Use This Visualization</h2>
            <p>
                <ul>
                    <li>Click on the links above to open different network visualizations</li>
                    <li>In the visualizations:</li>
                    <ul>
                        <li>Red nodes represent professors</li>
                        <li>Blue nodes represent coauthors</li>
                        <li>Green nodes represent shared coauthors (connected to multiple professors)</li>
                        <li>Orange edges between professors indicate shared collaborators</li>
                        <li>Hover over nodes for more information</li>
                        <li>Drag nodes to rearrange the network</li>
                        <li>Scroll to zoom in/out</li>
                    </ul>
                </ul>
            </p>
        </body>
        </html>
        """)
    
    print("\nCreated index.html with links to all network visualizations")

def main():
    # List of Google Scholar IDs (Replace with actual IDs)
    scholar_ids = ["1Yl1h_YAAAAJ", "UBXqggoAAAAJ", "bmQ917cAAAAJ", "W4lc9bUAAAAJ", "OGQm6cwAAAAJ"]
    
    # Extract all profiles
    print("Extracting scholar profiles...")
    profiles = [extract_scholar_profile(scholar_id) for scholar_id in scholar_ids]
    
    # Create directory for visualizations if it doesn't exist
    if not os.path.exists("visualizations"):
        os.makedirs("visualizations")
    os.chdir("visualizations")
    
    # Generate all visualizations
    print("\nGenerating network visualizations...")
    create_integrated_visualization(profiles)
    
    print("\nAll visualizations have been created in the 'visualizations' directory.")
    print("Open 'visualizations/index.html' in a web browser to view the networks.")

if __name__ == "__main__":
    main()