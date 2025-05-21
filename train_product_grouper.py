import pandas as pd
import joblib
from app import db, app
from app.models import Product, Category
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import re

# Funkcija, kas saīsina kategorijas ID uz 1. līmeni
def saisinat_kategoriju_id(kategorijas_id):
    daļas = kategorijas_id.split("-")
    return "-".join(daļas[:2]) if len(daļas) >= 2 else kategorijas_id


# Ielādē datus no datubāzes konkrētam veikalam
def ieladet_datus(veikals):
    produkti = Product.query.filter_by(store=veikals, currently_listed=True).all()
    df_produkti = pd.DataFrame([{
        "nosaukums": p.name,
        "kategorija_id": p.category_id
    } for p in produkti])

    df_produkti["kat_id_lvl1"] = df_produkti["kategorija_id"].apply(saisinat_kategoriju_id)

    # Atlasām kategorijas no datubāzes
    kategorijas = Category.query.filter_by(store=veikals).all()
    df_kategorijas = pd.DataFrame([{
        "id": c.id,
        "nosaukums": c.name
    } for c in kategorijas])

    df_kategorijas["id_lvl1"] = df_kategorijas["id"].apply(saisinat_kategoriju_id)

    df_kat_nosaukumi = df_kategorijas.drop_duplicates("id_lvl1")[["id_lvl1", "nosaukums"]]
    df_kat_nosaukumi = df_kat_nosaukumi.rename(columns={"nosaukums": "kat_nos_lvl1"})

    apvienots = df_produkti.merge(df_kat_nosaukumi, left_on="kat_id_lvl1", right_on="id_lvl1", how="left")

    return apvienots[["nosaukums", "kat_nos_lvl1"]].dropna()



# Funkcija, kas trenē klasifikatoru un novērtē tā precizitāti
def trenet_modeli(dati, veikala_nosaukums):
    print(f"\nTrenējam modeli veikalam: {veikala_nosaukums}\n")

    def notirit_tekstu(teksts):
        teksts = teksts.lower()
        teksts = re.sub(r"[^\w\s]", "", teksts)
        teksts = re.sub(r"\d+", "", teksts)
        return teksts.strip()

    dati["nosaukums"] = dati["nosaukums"].apply(notirit_tekstu)
    x = dati["nosaukums"]
    y = dati["kat_nos_lvl1"]

    x_tren, x_tests, y_tren, y_tests = train_test_split(x, y, test_size=0.2, random_state=42)

    vektorizetajs = TfidfVectorizer(max_features=3000, ngram_range=(1,2))
    x_tren_vekt = vektorizetajs.fit_transform(x_tren)
    x_tests_vekt = vektorizetajs.transform(x_tests)

    modelis = LogisticRegression(max_iter=1000)
    modelis.fit(x_tren_vekt, y_tren)


    y_prognoze = modelis.predict(x_tests_vekt)

    print("Precizitāte:", accuracy_score(y_tests, y_prognoze))
    print("\nKlasifikācijas pārskats:")
    print(classification_report(y_tests, y_prognoze, zero_division=0))

    joblib.dump(modelis, f"models/model_{veikala_nosaukums}.pkl")
    joblib.dump(vektorizetajs, f"models/vectorizer_{veikala_nosaukums}.pkl")
    print(f"Modelis un vektorizētājs saglabāts: {veikala_nosaukums}\n")


if __name__ == "__main__":
    veikali = ["barbora_lv", "barbora_lt", "rimi_lv", "rimi_lt"]
    with app.app_context():
        print("Pieejamie veikali:", ", ".join(veikali))
        izvele = input("Ievadi veikalu vai 'all': ").strip().lower()

        if izvele == "all":
            for veikals in veikali:
                dati = ieladet_datus(veikals)
                if not dati.empty:
                    trenet_modeli(dati, veikals)
        elif izvele in veikali:
            dati = ieladet_datus(izvele)
            if not dati.empty:
                trenet_modeli(dati, izvele)
        else:
            print("Nepareiza izvēle. Ievadi vienu no: lv / lt / all")
