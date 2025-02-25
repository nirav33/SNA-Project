import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Load IIT and NIT professor data
iit_df = pd.read_csv("iit_professor_citation_data.csv")
nit_df = pd.read_csv("nit_professor_citation_data.csv")

# Create graph
G = nx.Graph()

# Add IIT professors (Red)
iit_profs = set(iit_df.iloc[:, 0])
for prof in iit_profs:
    G.add_node(prof, color="red")

# Add NIT professors (Blue)
nit_profs = set(nit_df.iloc[:, 0])
for prof in nit_profs:
    G.add_node(prof, color="blue")

# Extract and add co-authors
iit_coauthors = set()
for coauthors in iit_df.iloc[:, -1]:  # Last column contains co-authors
    if isinstance(coauthors, str):
        coauthors = eval(coauthors) if coauthors.startswith("[") else []
        iit_coauthors.update(coauthors)

nit_coauthors = set()
for coauthors in nit_df.iloc[:, -1]:
    if isinstance(coauthors, str):
        coauthors = eval(coauthors) if coauthors.startswith("[") else []
        nit_coauthors.update(coauthors)

# Common co-authors (Green)
common_coauthors = iit_coauthors.intersection(nit_coauthors)
for author in common_coauthors:
    G.add_node(author, color="green")

# Other co-authors (Gray)
other_coauthors = (iit_coauthors.union(nit_coauthors)) - common_coauthors - iit_profs - nit_profs
for author in other_coauthors:
    G.add_node(author, color="gray")

# Add edges between professors and co-authors
for _, row in iit_df.iterrows():
    prof = row.iloc[0]
    if isinstance(row.iloc[-1], str):
        coauthors = eval(row.iloc[-1]) if row.iloc[-1].startswith("[") else []
        for coauthor in coauthors:
            G.add_edge(prof, coauthor)

for _, row in nit_df.iterrows():
    prof = row.iloc[0]
    if isinstance(row.iloc[-1], str):
        coauthors = eval(row.iloc[-1]) if row.iloc[-1].startswith("[") else []
        for coauthor in coauthors:
            G.add_edge(prof, coauthor)

# Draw the graph
plt.figure(figsize=(12, 8))
node_colors = [G.nodes[node]["color"] for node in G.nodes]

pos = nx.spring_layout(G, seed=42)  # Positioning for better visualization
nx.draw(G, pos, with_labels=True, node_size=50, font_size=6, node_color=node_colors, edge_color="gray", alpha=0.6)

# Show the plot
plt.title("Co-authorship Network between IIT and NIT Professors")
plt.show()