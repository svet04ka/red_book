import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///species_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER_STATIC'] = 'static/uploads/'  # Папка для загрузки изображений
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = SQLAlchemy(app)


# Модель данных
class Species(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    habitat = db.Column(db.String(150), nullable=False)
    image_path = db.Column(db.String(150), nullable=True)  # Поле для изображения
    status = db.Column(db.String(50), default='pending')

    def __repr__(self):
        return f'<Species {self.name}>'


# Создание таблиц в базе данных
with app.app_context():
    db.create_all()


# Главная страница
@app.route('/')
def home():
    return render_template('index.html')


# Страница с информацией о видах
@app.route('/species')
def species():
    species_data = Species.query.all()
    return render_template('species.html', species=species_data)


@app.route('/add_species', methods=['GET', 'POST'])
def add_species():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        habitat = request.form['habitat']
        status = 'pending'  # Requires verification

        # Process the image
        image = request.files['image']
        if image:
            # Ensure the static uploads folder exists
            if not os.path.exists(app.config['UPLOAD_FOLDER_STATIC']):
                os.makedirs(app.config['UPLOAD_FOLDER_STATIC'])

            # Save the image directly to the static/uploads folder
            image_path = os.path.join(app.config['UPLOAD_FOLDER_STATIC'], image.filename)
            try:
                image.save(image_path)
            except Exception as e:
                # Обработать ошибку загрузки изображения
                print(f"Ошибка загрузки изображения: {e}")
                return "Ошибка загрузки изображения", 500

            # Create a new Species object
            new_species = Species(
                name=name,
                description=description,
                habitat=habitat,
                image_path='uploads/' + image.filename,  # Правильный путь к изображениям
                status=status
            )

            db.session.add(new_species)
            db.session.commit()

            return redirect(url_for('species'))

    return render_template('add_species.html')


# Страница верификации данных (для администратора)
@app.route('/verification')
def verification():
    pending_species = Species.query.filter_by(status='pending').all()
    return render_template('verification.html', species=pending_species)


# Верификация вида (только для администраторов)
@app.route('/verify_species/<int:species_id>', methods=['POST'])
def verify_species(species_id):
    species = Species.query.get_or_404(species_id)
    species.status = 'verified'
    db.session.commit()
    return redirect(url_for('verification'))


if __name__ == '__main__':
    app.run(debug=True)