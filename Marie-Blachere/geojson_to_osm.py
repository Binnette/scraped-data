# Importer le module json pour lire et écrire des données JSON
import json
import codecs

# Importer le module xml.etree.ElementTree pour créer et manipuler des éléments XML
import xml.etree.ElementTree as ET

# Définir une fonction qui prend en entrée un fichier GeoJSON et renvoie un fichier OSM XML
def geojson2osm (geojson_file):

  # Ouvrir le fichier GeoJSON et charger les données JSON
  with open (geojson_file, "r", encoding='utf-8') as input_file:
    geojson_data = json.load (input_file)

  # Créer un élément racine osm avec les attributs version, generator et timestamp
  osm_root = ET.Element ("osm", {"version": "0.6", "generator": "python" })

  # Initialiser un compteur pour les identifiants des éléments OSM
  osm_id = 0

  # Parcourir les entités du fichier GeoJSON
  for feature in geojson_data ["features"]:

    # Obtenir le type de géométrie de l'entité (Point, LineString, Polygon, etc.)
    geometry_type = feature ["geometry"] ["type"]

    # Obtenir les coordonnées de l'entité sous forme de liste de tuples (lon, lat)
    coordinates = feature ["geometry"] ["coordinates"]

    # Obtenir les propriétés de l'entité sous forme de dictionnaire
    properties = feature ["properties"]

    # Créer une liste vide pour stocker les identifiants des nœuds OSM créés à partir des coordonnées
    node_ids = []

    # Si le type de géométrie est Point, créer un seul nœud OSM avec les coordonnées et les propriétés
    if geometry_type == "Point":

      # Incrémenter le compteur d'identifiant
      osm_id -= 1

      # Créer un élément node avec les attributs id, lon et lat
      node = ET.SubElement (osm_root, "node", {"id": str (osm_id), "lon": str (coordinates [0]), "lat": str (coordinates [1])})

      # Ajouter les propriétés comme des éléments tag avec les attributs k et v
      for key, value in properties.items ():
        tag = ET.SubElement (node, "tag", {"k": key, "v": str (value)})

    # Si le type de géométrie est LineString ou Polygon, créer plusieurs nœuds OSM avec les coordonnées et une relation OSM avec les propriétés
    elif geometry_type in ["LineString", "Polygon"]:

      # Parcourir les coordonnées de la géométrie
      for coordinate in coordinates:

        # Incrémenter le compteur d'identifiant
        osm_id += 1

        # Créer un élément node avec les attributs id, lon et lat
        node = ET.SubElement (osm_root, "node", {"id": str (osm_id), "lat": str (coordinate [1]), "lon": str (coordinate [0])})

        # Ajouter l'identifiant du nœud à la liste des identifiants des nœuds
        node_ids.append (osm_id)

      # Incrémenter le compteur d'identifiant
      osm_id += 1

      # Créer un élément relation avec l'attribut id
      relation = ET.SubElement (osm_root, "relation", {"id": str (osm_id)})

      # Ajouter les propriétés comme des éléments tag avec les attributs k et v
      for key, value in properties.items ():
        tag = ET.SubElement (relation, "tag", {"k": key, "v": str (value)})

      # Ajouter les identifiants des nœuds comme des éléments member avec les attributs type, ref et role
      for node_id in node_ids:
        member = ET.SubElement (relation, "member", {"type": "node", "ref": str (node_id), "role": ""})

  # Créer un objet ElementTree à partir de l'élément racine osm
  osm_tree = ET.ElementTree (osm_root)

  # Retourner l'objet ElementTree
  return osm_tree


tree = geojson2osm('marie_blachere.geojson')
tree.write("marie_blachere.osm", encoding="UTF-8", xml_declaration=True)
