from flask import Flask, render_template, url_for, request, redirect,session, Response
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import mariadb
import ast
import os


konekcija = mysql.connector.connect(
    passwd="",
    user="root",
    database="hotel",
    port=3306,
    auth_plugin='mysql_native_password'
)
kursor=konekcija.cursor(dictionary=True)


app = Flask(__name__)
# deklaracija upload direktorijuma
UPLOAD_FOLDER = "static/images/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

app.secret_key = "tajni_kljuc_aplikacije"

def ulogovan():
    if "ulogovani_korisnik" in session:
        return True
    else:
        return False
    
def rola():
    if ulogovan():
        return ast.literal_eval(session["ulogovani_korisnik"]).get("rola")




@app.route('/', methods=["GET"])
def render_naslovna():
    return render_template('naslovna.html', rola=rola())


@app.route('/o_nama', methods=["GET"])
def render_onama():
    return render_template('o_nama.html')

@app.route('/kontakt', methods=["GET"])
def render_kontakt():
    return render_template('kontakt.html')

@app.route('/prijava', methods=["GET","POST"])
def render_prijava():
    if request.method=="GET":
        return render_template("prijava.html")
    if request.method=="POST":
        forma=request.form
        upit="SELECT * FROM korisnici WHERE email=%s"
        vrednost=(forma["email"],)
        kursor.execute(upit, vrednost)
        korisnik=kursor.fetchone()
        if korisnik != None:
            if check_password_hash(korisnik["lozinka"], forma["lozinka"]):
                print("Lozinka ispravna!")
                print("Uloga korisnika:", korisnik["rola"])
                session["ulogovani_korisnik"] = str(korisnik)
                return redirect(url_for("render_naslovna"))
            else:
                print("Lozinka nije ispravna!")
                return render_template("prijava.html", error="Neispravna lozinka.")
        else:
            print("Korisnik nije pronađen!")
            return render_template("prijava.html", error="Korisnik nije pronađen.")


    return render_template("prijava.html")

@app.route('/rezervacija', methods=["GET", "POST"])
def render_rezervacija():
    if ulogovan():
        if request.method == "GET":
            return render_template("rezervacija.html", rola=rola())
        if request.method == "POST":
            forma = request.form
            
            vrednosti = (
                forma["ime"],
                forma["prezime"],
                forma["email"],
                int(forma["brojOdraslih"]),
                forma["tip"],
                forma["datumD"],
                forma["datumO"],
                forma["dorucak"],
                forma["svrha"],
                forma["poruka"]
            )

            upit = """INSERT INTO rezervacija
            (ime, prezime, email, broj_odraslih, tip, datum_dolaska, datum_odlaska, dorucak, svrha, poruka) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """ #nazivi u tabeli
            kursor.execute(upit, vrednosti)
            konekcija.commit()

            return redirect(url_for("render_naslovna"))
    else:
            return render_template("prijava.html")

@app.route('/novi_gost', methods=["GET","POST"])
def render_novi():
    #if rola()=="administrator"
    if request.method=="GET":
        return render_template("novi_gost.html")
    if request.method=="POST":
        forma=request.form
        hesovana_lozinka=generate_password_hash(forma["lozinka"])
        vrednosti=(
            forma["ime"],
            forma["prezime"],
            forma["email"],
            forma["rola"],
            hesovana_lozinka
         )

        upit="""insert into
            korisnici(ime,prezime,email,rola,lozinka)
            values(%s, %s, %s, %s, %s)
        """
        kursor.execute(upit, vrednosti)
        konekcija.commit()

        return redirect(url_for("render_naslovna")) #navodi gde zeli da ode


@app.route('/novi_korisnik', methods=["GET","POST"])
def render_korisnikNovi():
    if ulogovan():
        if rola()=='administrator':
            if request.method=="GET":
                return render_template("novi_korisnik.html")
            if request.method=="POST":
                forma=request.form
                hesovana_lozinka=generate_password_hash(forma["lozinka"])
                vrednosti=(
                    forma["ime"],
                    forma["prezime"],
                    forma["email"],
                    forma["rola"],
                    hesovana_lozinka
                )

                upit="""insert into
                    korisnici(ime,prezime,email,rola,lozinka)
                    values(%s, %s, %s, %s, %s)
                """
                kursor.execute(upit, vrednosti)
                konekcija.commit()

                return redirect(url_for("render_korisnici"))
        else:
                return render_template("prijava.html")
    
@app.route('/korisnik_izmena/<id>', methods=["GET","POST"])
def korisnik_izmena(id):
    if ulogovan():
        if rola() == 'administrator':
            if request.method == "GET":
                upit = "select * from korisnici where id=%s"
                vrednost = (id,)
                kursor.execute(upit, vrednost)
                korisnik = kursor.fetchone()

                return render_template("korisnik_izmena.html", korisnik=korisnik)
            elif request.method == "POST":
                upit = """UPDATE korisnici SET
                            ime=%s, prezime=%s, email=%s, rola=%s, lozinka=%s
                            WHERE id=%s
                        """

                forma = request.form
                vrednosti = (
                    forma["ime"],
                    forma["prezime"],
                    forma["email"],
                    forma["rola"],
                    forma["lozinka"],
                    id
                )
                kursor.execute(upit, vrednosti)
                konekcija.commit()
                return redirect(url_for('render_korisnici'))
        else:
            return render_template("prijava.html")
    else:
        return render_template("prijava.html")
    
@app.route('/korisnik_brisanje/<id>',methods=["POST"])
def korisnik_brisanje(id):
    if ulogovan():
        if rola()=='administrator':
            upit="""
                    DELETE FROM korisnici WHERE id=%s
                """
            vrednost=(id, )
            kursor.execute(upit, vrednost)
            konekcija.commit()
            return redirect(url_for("render_korisnici"))
        else:
                return render_template("prijava.html")
    else:
                return render_template("prijava.html")


@app.route('/rezervacija_brisanje/<id>',methods=["POST"])
def rezervacija_brisanje(id):
    if ulogovan():
        if rola() in ('administrator', 'recepcija'):
            upit="""
                    DELETE FROM rezervacija WHERE id=%s
                """
            vrednost=(id, )
            kursor.execute(upit, vrednost)
            konekcija.commit()
            return redirect(url_for("render_rezervacijaTabela"))
        else:
                return render_template("prijava.html")
    else:
                return render_template("prijava.html")


@app.route('/korisnici', methods=["GET"])
def render_korisnici():
    if ulogovan():
        if rola() in ('administrator', 'recepcija'):
            strana = request.args.get('strana', 1, type=int)
            velicina_strane = 3  # Broj korisnika po strani
            offset = (strana - 1) * velicina_strane

            # Prilagođeni upit za paginaciju
            upit = "SELECT * FROM korisnici LIMIT %s OFFSET %s"
            kursor.execute(upit, (velicina_strane, offset))
            korisnici = kursor.fetchall()

            return render_template('korisnici.html', korisnici=korisnici, rola=rola(), strana=strana)
        else:
            return render_template("prijava.html")
    else:
            return render_template("prijava.html")

@app.route('/rezervacija_tabela', methods=["GET"])
def render_rezervacijaTabela():
    if ulogovan():
        strana = request.args.get('strana', 1, type=int)
        velicina_strane = 10  # Broj rezultata po strani

        # Izračunajte offset (pomak) na osnovu trenutne strane
        offset = (strana - 1) * velicina_strane

        # SQL upit sa paginacijom
        upit = """SELECT * FROM rezervacija
                  LIMIT %s OFFSET %s"""

        # Izvršavanje upita sa vrednostima
        kursor.execute(upit, (velicina_strane, offset))
        rezervacija = kursor.fetchall()

        return render_template('rezervacija_tabela.html', rezervacija=rezervacija, rola=rola(), strana=strana)
    else:
        return render_template("prijava.html")

@app.route('/novasoba', methods=["GET", "POST"])
def render_novasoba():
    if ulogovan():
        if request.method == "GET":
            return render_template('novasoba.html')
        elif request.method == "POST":
            tip = request.form['tip']
            broj_slobodnih = request.form['broj_slobodnih']
            
            if 'slika' in request.files:
                slika = request.files['slika']
                if slika.filename != '':
                    slika_path = os.path.join(app.config['UPLOAD_FOLDER'], slika.filename)
                    slika.save(slika_path)

                    # Sačuvajte podatke u bazi podataka
                    upit = """INSERT INTO sobe (tip, slika, broj_slobodnih) VALUES (%s, %s, %s)"""
                    vrednosti = (tip, slika.filename, broj_slobodnih)
                    kursor.execute(upit, vrednosti)
                    konekcija.commit()
        
        return redirect(url_for("render_sobe"))
    else:
                return render_template("prijava.html")

@app.route('/sobe', methods=["GET"])
def render_sobe():
    # Dohvatite podatke iz baze podataka
    upit = "SELECT * FROM sobe"
    kursor.execute(upit)
    sobe_iz_baze = kursor.fetchall()

    # Prikazivanje podataka u HTML-u
    return render_template('sobe.html', sobe=sobe_iz_baze, rola=rola())

    
@app.route('/soba_brisanje/<id>',methods=["POST"])
def soba_brisanje(id):
    if ulogovan():
        upit="""
                DELETE FROM sobe WHERE id=%s
            """
        vrednost=(id, )
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("render_sobe"))

@app.route('/soba_izmena/<id>', methods=["GET", "POST"])
def soba_izmena(id):
    if ulogovan():
        if request.method == "GET":
            upit = "SELECT * FROM sobe WHERE id=%s"
            vrednost = (id,)
            kursor.execute(upit, vrednost)
            soba = kursor.fetchone()

            return render_template("soba_izmena.html", soba=soba)
        elif request.method == "POST":
            forma = request.form
            upit = """UPDATE sobe SET tip=%s, broj_slobodnih=%s WHERE id=%s"""

            vrednosti = (
                forma["tip"],
                forma["broj_slobodnih"],
                id
            )

            # Izvršavanje SQL upita za izmenu podataka
            kursor.execute(upit, vrednosti)
            konekcija.commit()

            # Nakon izmene, preusmerite korisnika na odgovarajuću stranicu, na primer, tabelu sa sobama
            return redirect(url_for("render_sobe"))
        else:
            # Ako request.method nije GET ili POST, vraćamo None
            return None
    else:
        return render_template("prijava.html")


@app.route('/rezervacija_izmena/<id>', methods=["GET","POST"])
def rezervacija_izmena(id):
    if ulogovan():
        if request.method == "GET":
            upit = "select * from rezervacija where id=%s"
            vrednost = (id, )
            kursor.execute(upit, vrednost)
            rezervacija = kursor.fetchone()

            return render_template("rezervacija_izmena.html", rezervacija=rezervacija)
        elif request.method == "POST":
            # Procesuirajte podatke iz forme i izvršite potrebne promene u bazi podataka
            forma = request.form
            upit = """ 
                UPDATE rezervacija SET 
                ime=%s, prezime=%s, email=%s, broj_odraslih=%s, tip=%s, 
                datum_dolaska=%s, datum_odlaska=%s, dorucak=%s, svrha=%s, poruka=%s 
                WHERE id=%s
            """

            vrednosti = (
                forma["ime"],
                forma["prezime"],
                forma["email"],
                forma["brojOdraslih"],
                forma["tip"],
                forma["datumD"],
                forma["datumO"],
                forma["dorucak"],
                forma["svrha"],
                forma["poruka"],
                id
            )

            kursor.execute(upit, vrednosti)
            konekcija.commit()

            # Nakon izmena, preusmerite korisnika na odgovarajuću stranicu, na primer, tabelu sa rezervacijama
            return redirect(url_for("render_rezervacijaTabela"))
    else:
        return render_template("prijava.html")


@app.route('/odjava')
def odjava():
    session.pop('ulogovani_korisnik',None)
    return redirect(url_for('render_prijava'))


   
app.run(debug=True)
