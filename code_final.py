# %% [markdown]
# 0. IMPORTER LES LIBRAIRIES

# %%
import os
import re
import json
import pandas as pd
from bs4 import BeautifulSoup

# %% [markdown]
# 1. CONFIGURATION

# %%
DOSSIER_SORTIE = os.path.dirname(os.path.abspath(__file__))
NOM_DOSSIER_HTML = "deliveroo" 
DOSSIER_HTML = os.path.join(DOSSIER_SORTIE, NOM_DOSSIER_HTML)

# %% [markdown]
# 2. FONCTIONS UTILITAIRES
# 
# Fonction pour nettoyer les balises HTML et les caractères spéciaux.

# %%
def clean_text(tag):
    if tag:
        return tag.get_text(strip=True).replace('\xa0', ' ').replace('&amp;', '&')
    return ""

# %% [markdown]
# Fonction pour lire un fichier HTML et extrait la liste des articles commandés.

# %%
def extract_data_from_html(filepath, filename):
    items_extracted = []
    # Ouverture et analyse du fichier HTML avec BeautifulSoup
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

        # A. INFO COMMANDE
        # Extrait la date depuis le nom du fichier et l'ID de commande via le texte "Commande n°"
        raw_date = filename.split('.')[0].replace('_', ' ')
        cmd_tag = soup.find(string=re.compile("Commande n°"))
        order_number = cmd_tag.strip().split(' ')[-1] if cmd_tag else "N/A"

        # B. ADRESSES (RESTAURANT & CLIENT)
        fluid_tables = soup.find_all('table', class_='fluid')
        r_data = [""] * 5 # Initialise les listes pour : Nom, Adresse, Ville, Code Postal, Tel
        c_data = [""] * 5 

        if len(fluid_tables) >= 3:
            # Restaurant
            p_rest = fluid_tables[0].find_all('p')
            if p_rest:
                r_data = [clean_text(p) for p in p_rest[:5]]
                r_data += [""] * (5 - len(r_data)) # Ajoute des vides si moins de 5 lignes trouvées

            # Client (même logique que pour le restaurant)
            p_cust = fluid_tables[2].find_all('p')
            if p_cust:
                c_data = [clean_text(p) for p in p_cust[:5]]
                c_data += [""] * (5 - len(c_data))

        # C. PRIX & FRAIS DE LIVRAISON
        # Cherche le label "Total", remonte à la cellule parente, puis prend la cellule suivante (le prix)
        total_paid = "0"
        total_tag = soup.find('p', class_='total')
        if total_tag and total_tag.find_parent('td'):
            next_td = total_tag.find_parent('td').find_next_sibling('td')
            if next_td: total_paid = clean_text(next_td)
        
        # Même logique de navigation pour les frais de livraison
        delivery_fee = "0"
        del_tag = soup.find(string=re.compile("Frais de livraison"))
        if del_tag and del_tag.find_parent('td'):
            next_td = del_tag.find_parent('td').find_next_sibling('td')
            if next_td: delivery_fee = clean_text(next_td)

        # D. ARTICLES
        # Identifie les lignes d'articles via la largeur de cellule fixe (width="40")
        qty_cells = soup.find_all('td', width="40")
        for qty_cell in qty_cells:
            row = qty_cell.find_parent('tr') # Récupère toute la ligne
            cols = row.find_all('td') # Récupère les colonnes
            if len(cols) >= 3: # Extraction : Quantité (col 1), Nom (col 2), Prix (col 3)
                qty = clean_text(cols[0]).lower().replace('x', '')
                item_name_cell = cols[1]
                item_name = clean_text(item_name_cell.find('p')) if item_name_cell.find('p') else clean_text(item_name_cell)
                item_price = clean_text(cols[2])
                
                # Ajoute l'article à la liste finale avec TOUTES les infos de la commande (date, adresses, etc.)
                items_extracted.append({
                    'Date_File': raw_date,
                    'Order_ID': order_number,
                    'Total_Paid': total_paid,
                    'Delivery_Fee': delivery_fee,
                    'Rest_Name': r_data[0], 'Rest_Address': r_data[1], 'Rest_City': r_data[2], 'Rest_Zip': r_data[3], 'Rest_Phone': r_data[4],
                    'Cust_Name': c_data[0], 'Cust_Address': c_data[1], 'Cust_City': c_data[2], 'Cust_Zip': c_data[3], 'Cust_Phone': c_data[4],
                    'Item_Qty': qty, 'Item_Name': item_name, 'Item_Price': item_price
                })

    return items_extracted

# %% [markdown]
# Fonction pour transformer le DataFrame en structure JSON.

# %%
def generate_hierarchical_json(df, output_path):
    json_output = []

    # 1. Regroupe les lignes par numéro de commande
    for order_id, group in df.groupby('Order_ID'):
        # 2. Récupère les informations communes (Date, Resto, Client)
        first = group.iloc[0]
        # 3. Construit la structure JSON principale pour cette commande
        order_obj = {
            "order": {
                "order_datetime": first['Date_File'],
                "order_number": first['Order_ID'],
                "delivery_fee": first['Delivery_Fee'],
                "order_total_paid": first['Total_Paid']
            },
            "restaurant": {
                "name": first['Rest_Name'],
                "address": first['Rest_Address'],
                "city": first['Rest_City'],
                "postcode": first['Rest_Zip'],
                "phone_number": first['Rest_Phone']
            },
            "customer": {
                "name": first['Cust_Name'],
                "address": first['Cust_Address'],
                "city": first['Cust_City'],
                "postcode": first['Cust_Zip'],
                "phone_number": first['Cust_Phone']
            },
            "order_items": [] # Liste vide pour les articles
        }
        # 4. Boucle sur chaque ligne du groupe pour lister les articles
        for _, row in group.iterrows():
            order_obj["order_items"].append({
                "name": row['Item_Name'],
                "quantity": row['Item_Qty'],
                "price": row['Item_Price']
            })
        # Ajoute la commande complète à la liste finale
        json_output.append(order_obj)
    # 5. Sauvegarde le résultat dans un fichier JSON propre et lisible
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=4)
    
    return len(json_output)

# %% [markdown]
# 3. EXÉCUTION DES FONCTIONS

# %%
# Création du dossier de sortie
if not os.path.exists(DOSSIER_HTML):
    os.makedirs(DOSSIER_HTML)

# Récupération des fichiers
fichiers = [f for f in os.listdir(DOSSIER_HTML) if f.endswith('.html')]

all_data = []

# Boucle principale
for fichier in fichiers:
    
    path = os.path.join(DOSSIER_HTML, fichier)
    data = extract_data_from_html(path, fichier)
    all_data.extend(data)

# Création du DataFrame
df = pd.DataFrame(all_data)

# 1. Export CSV
csv_path = os.path.join(DOSSIER_SORTIE, 'deliveroo_data_complet.csv')
df.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"CSV sauvegardé : {csv_path}")

# 2. Export JSON
json_path = os.path.join(DOSSIER_SORTIE, 'deliveroo_structure_finale.json')
nb_commandes = generate_hierarchical_json(df, json_path)
print(f"JSON sauvegardé : {json_path}")