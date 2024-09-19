import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.functions import current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///species_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки для загрузки изображений
app.config['UPLOAD_FOLDER_STATIC'] = 'static/uploads/'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.secret_key = 'q1w2e3'

db = SQLAlchemy(app)

class PendingSpecies(db.Model):
    __tablename__ = 'pending_species'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    habitat = db.Column(db.String(150), nullable=False)
    image_path = db.Column(db.String(150), nullable=True)  # Поле для изображения
    status = db.Column(db.String(50), default='pending')
    rarity = db.Column(db.String(100), nullable=False)
    coords = db.Column(db.String(50), nullable=False)
    species_type = db.Column(db.String(50), nullable=False)  # Растение или животное
    species_class = db.Column(db.String(50), nullable=False)  # Класс
    family = db.Column(db.String(50), nullable=False)  # Семейство

    def __repr__(self):  # Исправлено на __repr__
        return f'<Species {self.name}>'


class Species(db.Model):
    __tablename__ = 'species_data'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    habitat = db.Column(db.String(150), nullable=False)
    image_path = db.Column(db.String(150), nullable=True)  # Поле для изображения
    status = db.Column(db.String(50), default='pending')
    rarity = db.Column(db.String(100), nullable=False)
    coords = db.Column(db.String(50), nullable=False)
    species_type = db.Column(db.String(50), nullable=False)  # Растение или животное
    species_class = db.Column(db.String(50), nullable=False)  # Класс
    family = db.Column(db.String(50), nullable=False)


# Создание таблиц в базе данных
with app.app_context():
    db.create_all()

db_path = 'instance/users.db'



@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    # Проверка аутентификации
    if role == "admin":
        # Проверка в базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND type = 'admin'", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user[2] == password:  # Проверка пароля из базы данных
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('verification_page'))
        else:
            return redirect(url_for('home'))

    elif role == "dep":
        # Проверка в базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND type = 'dep'", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user[2] == password:  # Проверка пароля из базы данных
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('department_page'))
        else:
            return redirect(url_for('home'))

    return redirect(url_for('home'))



@app.route('/verification')
def verification_page():
    if 'logged_in' in session and session['logged_in']:
        pending_species = PendingSpecies.query.all()
        return render_template('verification.html', pending_species=pending_species)
    else:
        return redirect(url_for('home'))


@app.route('/department')
def department_page():
    if 'logged_in' in session and session['logged_in']:
        return render_template('department.html')
    else:
        return redirect(url_for('home'))


# Маршрут для выхода из системы
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))


# Главная страница
@app.route('/')
def home():
    return render_template('index.html')


# Страница с информацией о видах
@app.route('/species')
def species():
    species_data = Species.query.all()
    return render_template('species.html', species=species_data)

@app.route('/species_for_dep')
def species_for_dep():
    species_data = Species.query.all()
    return render_template('species_for_dep.html', species=species_data)

@app.route('/add_species', methods=['GET', 'POST'])
def add_species():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        habitat = request.form['habitat']
        species_type = request.form['type']
        rarity = request.form['rarity']
        coords = request.form['coords']
        species_class = request.form['class']
        family = request.form['family']

        # Обработка изображения
        image = request.files['image']
        if image:
            if not os.path.exists(app.config['UPLOAD_FOLDER_STATIC']):
                os.makedirs(app.config['UPLOAD_FOLDER_STATIC'])

                # Save the image directly to the static/uploads folder
            image_path = os.path.join(app.config['UPLOAD_FOLDER_STATIC'], image.filename)
            try:
                image.save(image_path)
            except Exception as e:
                print(f"Ошибка загрузки изображения: {e}")
                return "Ошибка загрузки изображения", 500
            new_species = PendingSpecies(
                name=name,
                description=description,
                habitat=habitat,
                image_path='uploads/' + image.filename,
                rarity=rarity,
                coords=coords,
                species_type=species_type,
                species_class=species_class,
                family=family
            )

            # Сохранение записи в таблицу "pending_species"
            db.session.add(new_species)
            db.session.commit()
            flash("Отправлено админу")

            return redirect(url_for('species'))

    return render_template('add_species.html')

@app.route('/verification', methods=['GET', 'POST'])
def verification():
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            species_id = request.form.get('species_id')
            action = request.form.get('action')  # 'approve' or 'reject'

            with sqlite3.connect('instance/species_data.db') as conn:
                cursor = conn.cursor()

                if action == 'approve':
                    # Обновление статуса записи в таблице pending_species
                    cursor.execute("UPDATE pending_species SET status = 'approved' WHERE id = ?", (species_id,))
                    conn.commit()

                    # Перенос одобренной записи в таблицу "species_data"
                    cursor.execute(
                        "INSERT INTO species_data (name, description, habitat, image_path, rarity, coords, species_type, species_class, family) "
                        "SELECT name, description, habitat, image_path, rarity, coords, species_type, species_class, family "
                        "FROM pending_species WHERE id = ?",
                        (species_id,)
                    )
                    conn.commit()

                    # Удаление записи из pending_species
                    cursor.execute("DELETE FROM pending_species WHERE id = ?", (species_id,))
                    conn.commit()

                    flash('Запись успешно одобрена!', 'success')

                elif action == 'reject':
                    # Удаление записи из таблицы pending_species
                    cursor.execute("DELETE FROM pending_species WHERE id = ?", (species_id,))
                    conn.commit()

                    flash('Запись отклонена', 'info')

            # После выполнения POST-запроса всегда делаем редирект на ту же страницу
            return redirect(url_for('verification'))

        # При GET-запросе загружаем список непроверенных записей
        with sqlite3.connect('instance/species_data.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pending_species WHERE status = 'pending'")
            pending_species = cursor.fetchall()

        return render_template('verification.html', pending_species=pending_species)
    else:
        return redirect(url_for('home'))

@app.route('/edit_specie/<int:specie_id>', methods=['GET', 'POST'])
def edit_specie(specie_id):
    specie = Species.query.get_or_404(specie_id)

    if request.method == 'POST':
        specie.name = request.form['name']
        specie.description = request.form['description']
        specie.habitat = request.form['habitat']
        specie.rarity = request.form['rarity']
        species_type = request.form['type']
        specie.coords = request.form['coords']
        specie.species_class = request.form['class']
        specie.family = request.form['family']

        # Обработка изображения

        db.session.commit()
        return redirect(url_for('species_for_dep'))



    return render_template('edit_specie.html', specie=specie)



if __name__ == '__main__':
    app.run(debug=True)  # Запуск Flask в режиме отладки
