#!/bin/bash

# Siirrytään skriptin hakemistoon varmistaaksesi, että polut ovat oikein.
# Tämä on tärkeää, jos skriptiä ajetaan muualta kuin sen omasta hakemistosta.
cd "$(dirname "$0")"

echo "Käynnistetään kuvien optimointiohjelma..."

# Aktivoidaan Pythonin virtuaaliympäristö
source venv/bin/activate

# Käynnistetään Python-skripti
python image_optimizer.py

echo "Ohjelma käynnistetty. Sulje ikkuna ohjelman sulkemisen jälkeen."

# Pysäytetään terminaali, jotta käyttäjä näkee mahdolliset virheilmoitukset.
read -p "Paina Enter jatkaaksesi..."
