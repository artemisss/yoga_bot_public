from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flasgger import Swagger
from swagger import swagger_template  # Подключаем swagger_template
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

swagger = Swagger(app, template=swagger_template)


app.secret_key = os.environ.get('SECRET_KEY')

from functools import wraps

API_KEY = os.environ.get('API_KEY')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')  # получаем api_key из заголовка
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized"}), 401
    return decorated_function


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    telegram_id = db.Column(db.BigInteger)
    employee_id = db.Column(db.String(255))
    role = db.Column(db.String(50), nullable=False)
    info = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    office = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=True)  # Ссылка на ID офиса

class EventRegistration(db.Model):
    __tablename__ = 'event_registration'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Добавление связи с User
    user = db.relationship('User', backref='registrations', lazy=True)
    event = db.relationship('Event', backref='registrations', lazy=True)

class Office(db.Model):
    __tablename__ = 'offices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)

    # Опционально, если вы хотите использовать обратную связь от офисов к событиям
    events = db.relationship('Event', backref='office', lazy=True)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    coach = db.Column(db.String(255), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=False)
    max_participants = db.Column(db.Integer, nullable=False)

class Coach(db.Model):
    __tablename__ = 'coaches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


@app.route('/users', methods=['POST'])
@require_api_key
def create_user():
    data = request.get_json()

    # Проверяем, существует ли уже пользователь с таким telegram_id
    existing_user = User.query.filter_by(telegram_id=data['telegram_id']).first()
    if existing_user:
        return jsonify({
                           'error': 'Пользователь уже зарегистрирован'}), 409  # Код 409 Conflict для ситуаций, когда возникает конфликт данных

    # Если пользователя с таким telegram_id нет, создаем нового
    user = User(
        name=data['name'],
        telegram_id=data['telegram_id'],
        employee_id=data.get('employee_id', None),
        # Используем get для обработки случаев, когда employee_id не предоставлен
        role=data['role'],
        info=data.get('info', {})  # Аналогично обрабатываем отсутствие info
    )
    db.session.add(user)
    try:
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {'error': str(e)}), 500  # В случае ошибки при сохранении возвращаем код 500 и информацию об ошибке
@app.route('/users/info/<int:telegram_id>', methods=['GET', 'PUT']) # чтение и рпедактирование поля info
def user_info(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    if request.method == 'GET':
        # Возвращаем текущее значение поля info
        return jsonify(user.info or {}), 200

    elif request.method == 'PUT':
        # Обновляем значение поля info
        data = request.get_json()
        new_info = data.get('info')
        if new_info is not None and isinstance(new_info, dict):
            if user.info is None:
                user.info = {}
            user.info.update(new_info)
            db.session.commit()
            return jsonify({'message': 'Информация пользователя успешно обновлена'}), 200
        else:
            return jsonify({'error': 'Некорректные данные для поля info'}), 400

@app.route('/users/is_registered/<int:telegram_id>', methods=['GET']) # проверка что пользователь зарегистрирован
def is_user_registered(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first()
    return jsonify({'is_registered': user is not None}), 200


@app.route('/users/update_by_telegram_id', methods=['PUT'])
@require_api_key
def update_user_by_telegram_id():
    data = request.get_json()
    telegram_id = data.get('telegram_id')

    # Проверяем наличие telegram_id в запросе
    if not telegram_id:
        return jsonify({'error': 'Необходимо указать telegram_id'}), 400

    # Находим пользователя по telegram_id
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    # Обновляем поля пользователя, за исключением telegram_id
    user.name = data.get('name', user.name)
    user.employee_id = data.get('employee_id', user.employee_id)
    user.role = data.get('role', user.role)
    user.info = data.get('info', user.info)

    # Сохраняем изменения
    try:
        db.session.commit()
        return jsonify({'message': 'Данные пользователя успешно обновлены'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/coaches', methods=['GET'])
def get_coaches():
    coaches = Coach.query.all()
    return jsonify([coach.to_dict() for coach in coaches]), 200


@app.route('/event_registrations', methods=['POST']) # Регистрация пользователя на событие
@require_api_key
def create_event_registration():
    data = request.get_json()
    event_id = data.get('event_id')
    telegram_id = data.get('telegram_id')

    # Проверяем, существует ли событие
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'События не существует'}), 404

    # Проверяем, существует ли пользователь по telegram_id
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'error': 'Пользователя не существует'}), 404

    # Проверяем, записан ли пользователь уже на это конкретное событие
    existing_registration = EventRegistration.query.filter_by(user_id=user.id, event_id=event_id).first()
    if existing_registration:
        return jsonify({'error': 'Пользователь уже зарегистрировался на это событие'}), 400

    # Проверяем, есть ли свободные места на событии
    registered_count = EventRegistration.query.filter_by(event_id=event_id).count()
    if registered_count >= event.max_participants:
        return jsonify({'error': 'На это событие все места уже заняты'}), 400

    # Проверяем, не закончилось ли уже событие
    now = datetime.now()
    event_datetime = datetime.combine(event.date, event.time)
    if now >= event_datetime:
        return jsonify({'error': 'Нельзя зарегистрироваться на событие, которое уже закончилось'}), 400

    # Создаем запись на событие
    event_registration = EventRegistration(event_id=event_id, user_id=user.id)
    db.session.add(event_registration)
    try:
        db.session.commit()
        return jsonify({'message': 'Вы успешно зарегистрированы на событие'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@app.route('/event_registrations/delete', methods=['POST'])
@require_api_key
def delete_event_registration():
    data = request.get_json()
    event_id = data.get('event_id')
    telegram_id = data.get('telegram_id')

    # Находим пользователя по telegram_id
    user = User.query.filter_by(telegram_id=telegram_id).first()

    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    # Ищем запись на событие по event_id и user_id
    event_registration = EventRegistration.query.filter_by(event_id=event_id, user_id=user.id).first()

    # Если запись на событие не найдена, возвращаем ошибку
    if not event_registration:
        return jsonify({'error': 'Вы не подписаны на это событие'}), 404

    # Удаляем запись на событие
    db.session.delete(event_registration)
    try:
        db.session.commit()
        return jsonify({'message': 'Регистрация на событие удалена'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


from sqlalchemy.sql import func, expression

@app.route('/upcoming_events', methods=['GET']) # Предстоящие события
@require_api_key
def get_upcoming_events():
    # Объединяем date и time в одно значение datetime на уровне запроса
    datetime_expr = expression.cast(Event.date, db.DateTime) + expression.cast(Event.time, db.Interval)

    results = db.session.query(
        Event.id,
        datetime_expr.label('datetime'),
        Office.name.label('office_name'),
        func.count(EventRegistration.id).label('registered_participants'),
        Event.max_participants
    ).join(Office, Event.office_id == Office.id
    ).outerjoin(EventRegistration, EventRegistration.event_id == Event.id
    ).filter(
        datetime_expr >= func.now()  # Фильтруем события, начиная с текущего момента
    ).group_by(
        Event.id, Office.name, Event.max_participants, datetime_expr
    ).order_by(
        datetime_expr.asc()
    ).limit(20).all()

    upcoming_events = [
        {
            'event_id': event.id,
            'datetime': event.datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'office_name': event.office_name,
            'registered_participants': event.registered_participants,
            'max_participants': event.max_participants
        }
        for event in results
    ]

    return jsonify(upcoming_events)


@app.route('/available_events', methods=['GET'])  # Только события доступные для пользователя
@require_api_key
def get_available_events():
    # Получаем telegram_id пользователя из параметров запроса
    telegram_id = request.args.get('telegram_id')

    if not telegram_id:
        return jsonify({'error': 'Необходимо указать telegram_id пользователя'}), 400

    # Находим пользователя по telegram_id
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    datetime_expr = expression.cast(Event.date, db.DateTime) + expression.cast(Event.time, db.Interval)

    # Получаем ID событий, на которые пользователь уже зарегистрирован
    registered_event_ids = db.session.query(EventRegistration.event_id).filter_by(user_id=user.id).subquery()

    query = db.session.query(
        Event.id,
        datetime_expr.label('datetime'),
        Office.name.label('office_name'),
        Event.coach,
        func.count(EventRegistration.id).label('registered_participants'),
        Event.max_participants,
        Coach.name.label('coach_name'),
        Coach.description.label('coach_description')
    ).join(Office, Event.office_id == Office.id
    ).outerjoin(EventRegistration, EventRegistration.event_id == Event.id
    ).outerjoin(Coach, Coach.name == Event.coach
    ).filter(
        datetime_expr >= func.now(),
        ~Event.id.in_(registered_event_ids)
    )

    # Применяем фильтрацию по офису только если у пользователя указан любимый офис
    if user.office:
        query = query.filter(Event.office_id == user.office)

    results = query.group_by(
        Event.id, Office.name, Event.max_participants, datetime_expr, Coach.name, Coach.description
    ).order_by(
        datetime_expr.asc()
    ).limit(8).all()

    available_events = [
        {
            'event_id': event.id,
            'datetime': event.datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'office_name': event.office_name,
            'registered_participants': event.registered_participants,
            'max_participants': event.max_participants,
            'coach_name': event.coach_name,
            'coach_description': event.coach_description
        }
        for event in results
    ]

    return jsonify(available_events)


from flask import request, jsonify
from datetime import datetime


from datetime import datetime, time

@app.route('/user_events', methods=['GET'])  # События, на которые подписался пользователь
@require_api_key
def get_user_events():
    telegram_id = request.args.get('telegram_id')

    if not telegram_id:
        return jsonify({'error': 'Необходимо указать telegram_id пользователя'}), 400

    # Находим пользователя по telegram_id
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    # Теперь флаг future_events всегда True, так как мы хотим видеть только будущие события
    future_events = True

    query = db.session.query(
        EventRegistration,
        Event.date,
        Event.time,
        Office.name.label('office_name'),
        Event.coach,
        Event.max_participants
    ).join(Event, Event.id == EventRegistration.event_id
           ).join(Office, Office.id == Event.office_id
                  ).filter(EventRegistration.user_id == user.id)

    if future_events:
        now = datetime.now()
        # Объединяем дату и время события и сравниваем с текущим временем
        query = query.filter(
            (Event.date > now.date()) | ((Event.date == now.date()) & (Event.time > now.time())))

    registrations = query.all()

    if not registrations:
        return jsonify({'message': 'No events found for this user.'}), 404

    user_events = [
        {
            'event_id': registration.EventRegistration.event_id,
            'event_date': registration.date.isoformat(),
            'event_time': registration.time.strftime('%H:%M'),
            'office_name': registration.office_name,
            'coach': registration.coach,
            'max_participants': registration.max_participants
        }
        for registration in registrations
    ]

    return jsonify(user_events)

from sqlalchemy.sql import func

from datetime import datetime


@app.route('/upcoming_event_registrations', methods=['GET'])
@require_api_key
def get_upcoming_event_registrations():
    # Получаем текущее время
    now = datetime.now()

    # Формируем запрос к базе данных, фильтруя события, которые еще не произошли
    upcoming_events_query = db.session.query(
        Event.id,
        Event.date,
        Event.time,
        Office.name.label('office_name')
    ).join(Office, Event.office_id == Office.id
           ).filter(
        db.or_(
            db.and_(Event.date == now.date(), Event.time > now.time()),
            Event.date > now.date()
        )
    ).order_by(Event.date.asc(), Event.time.asc()
               ).limit(10)

    event_registrations = []
    for event in upcoming_events_query:
        registrations = db.session.query(
            User.name,
            EventRegistration.event_id,
            Event.date,
            Event.time,
            Office.name.label('office_name')
        ).join(EventRegistration, EventRegistration.user_id == User.id
               ).join(Event, EventRegistration.event_id == Event.id
                      ).join(Office, Event.office_id == Office.id
                             ).filter(EventRegistration.event_id == event.id
                                      ).all()

        for registration in registrations:
            event_registrations.append({
                'user_name': registration.name,
                'event_id': registration.event_id,
                'event_date': registration.date.isoformat(),
                'event_time': registration.time.strftime('%H:%M'),
                'office_name': registration.office_name
            })

    return jsonify(event_registrations)

@app.route('/users/office/<int:telegram_id>', methods=['GET'])
@require_api_key
def get_user_office(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    if user.office:
        office_info = {'office_id': user.office}
        return jsonify(office_info), 200
    else:
        return jsonify({'message': 'У пользователя не установлен любимый офис'}), 404


@app.route('/users/office/<int:telegram_id>', methods=['PUT'])
@require_api_key
def update_user_office(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    data = request.get_json()
    office_id = data.get('office_id')
    if office_id is None or not isinstance(office_id, int):
        return jsonify({'error': 'Некорректный формат ID офиса. Ожидается целое число.'}), 400

    user.office = office_id

    try:
        db.session.commit()
        return jsonify({'message': 'Любимый офис пользователя успешно обновлён'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Дальше админка

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

class EventModelView(ModelView):
    form_columns = ['date', 'time', 'coach', 'office_id', 'max_participants']


from flask_admin.contrib.sqla import ModelView


class EventRegistrationModelView(ModelView):
    column_list = ('id', 'user', 'event.office', 'event.coach', 'event.date', 'event.time')
    column_sortable_list = (
    'id', ('user', 'user.name'), ('event.office', 'event.office.name'), ('event.coach', 'event.coach'),
    ('event.date', 'event.date'), ('event.time', 'event.time'))

    def _user_formatter(view, context, model, name):
        # Убедитесь, что обращение к связанному пользователю корректно
        return model.user.name if model.user else ''

    column_formatters = {
        'user': _user_formatter,
    }

    column_labels = {
        'user': 'User Name',
        'event.office': 'Office Name',
        'event.coach': 'Coach',
        'event.date': 'Date',
        'event.time': 'Time'
    }

    def _user_formatter(view, context, model, name):
        if model.user:
            return model.user.name
        return ''

    def _office_formatter(view, context, model, name):
        if model.event and model.event.office:
            return model.event.office.name
        return ''

    column_formatters = {
        'user': _user_formatter,
        'event.office': _office_formatter,
    }

# Создание экземпляра административного интерфейса
admin = Admin(app, name='MyApp Admin', template_mode='bootstrap3')

# Добавление моделей в административный интерфейс
admin.add_view(ModelView(User, db.session))
admin.add_view(EventRegistrationModelView(EventRegistration, db.session, name='Заявки на йогу'))
admin.add_view(ModelView(Office, db.session))
admin.add_view(EventModelView(Event, db.session))



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)