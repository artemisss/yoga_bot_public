swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Yoga Bot API",
        "description": "API for managing users and yoga events",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": [
        "http"
    ],
    "paths": {
        "/users": {
            "post": {
                "summary": "Создать нового пользователя в БД",
                "description": "Создать нового пользователя в БД. Создав пользователя можно дальше регистрироваться на события",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    },
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "telegram_id": {"type": "integer"},
                                "employee_id": {"type": "string"},
                                "role": {"type": "string"},
                                "info": {"type": "object"}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {"description": "User created successfully"},
                    "409": {"description": "User already registered"},
                    "500": {"description": "Internal Server Error"}
                }
            }
        },
        "/users/info/{telegram_id}": {
            "get": {
                "summary": "Получить данные о пользователей",
                "description": "Получить данные о пользователе храняшиеся в JSON объекте",
                "parameters": [
                    {
                        "name": "telegram_id",
                        "in": "path",
                        "type": "integer",
                        "required": True,
                        "description": "Telegram ID of the user"
                    }
                ],
                "responses": {
                    "200": {"description": "Success"},
                    "404": {"description": "User not found"}
                }
            },
            "put": {
                "summary": "Обновить данные о пользователе",
                "description": "Updates the info field of the user",
                "parameters": [
                    {
                        "name": "telegram_id",
                        "in": "path",
                        "type": "integer",
                        "required": True,
                        "description": "Telegram ID of the user"
                    },
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "info": {"type": "object"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "User info updated successfully"},
                    "400": {"description": "Invalid data for info field"},
                    "404": {"description": "User not found"}
                }
            }
        },
        "/users/is_registered/{telegram_id}": {
            "get": {
                "summary": "Проверить что пользователь зарегистрирован",
                "description": "Checks if a user with the given Telegram ID is registered",
                "parameters": [
                    {
                        "name": "telegram_id",
                        "in": "path",
                        "type": "integer",
                        "required": True,
                        "description": "Telegram ID of the user"
                    }
                ],
                "responses": {
                    "200": {"description": "User registration status"}
                }
            }
        },
        "/users/update_by_telegram_id": {
            "put": {
                "summary": "Обновить множество данных о пользователе",
                "description": "Updates user data by Telegram ID",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    },
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "telegram_id": {"type": "integer"},
                                "name": {"type": "string"},
                                "employee_id": {"type": "string"},
                                "role": {"type": "string"},
                                "info": {"type": "object"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "User data updated successfully"},
                    "404": {"description": "User not found"},
                    "500": {"description": "Internal Server Error"}
                }
            }
        },
        "/coaches": {
            "get": {
                "summary": "Список тренеров",
                "description": "Retrieves a list of all coaches",
                "responses": {
                    "200": {"description": "List of coaches"}
                }
            }
        },
        "/event_registrations": {
            "post": {
                "summary": "Регистрация на событие",
                "description": "Registers a user for an event",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    },
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "integer"},
                                "telegram_id": {"type": "integer"}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {"description": "User registered for event successfully"},
                    "404": {"description": "Event or User not found"},
                    "400": {"description": "User already registered or event full or event ended"},
                    "500": {"description": "Internal Server Error"}
                }
            }
        },
        "/event_registrations/delete": {
            "post": {
                "summary": "Отмена регистрации на событие",
                "description": "Deletes a user's registration for an event",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    },
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "integer"},
                                "telegram_id": {"type": "integer"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "Event registration deleted successfully"},
                    "404": {"description": "User or registration not found"},
                    "500": {"description": "Internal Server Error"}
                }
            }
        },
        "/upcoming_events": {
            "get": {
                "summary": "Получить предстоящие события",
                "description": "Retrieves a list of upcoming events",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    }
                ],
                "responses": {
                    "200": {"description": "List of upcoming events"}
                }
            }
        },
        "/available_events": {
            "get": {
                "summary": "Получить событие которые доступны для конкретного пользователя",
                "description": "Retrieves a list of available events for a user",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    },
                    {
                        "name": "telegram_id",
                        "in": "query",
                        "type": "integer",
                        "required": True,
                        "description": "Telegram ID of the user"
                    }
                ],
                "responses": {
                    "200": {"description": "List of available events"},
                    "404": {"description": "User not found"},
                    "400": {"description": "User telegram_id is required"}
                }
            }
        },
        "/user_events": {
            "get": {
                "summary": "Список событий на которые зарегистрирован пользователь",
                "description": "Retrieves a list of events the user is registered for",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    },
                    {
                        "name": "telegram_id",
                        "in": "query",
                        "type": "integer",
                        "required": True,
                        "description": "Telegram ID of the user"
                    }
                ],
                "responses": {
                    "200": {"description": "List of events the user is registered for"},
                    "404": {"description": "User not found or no events found for this user"},
                    "400": {"description": "User telegram_id is required"}
                }
            }
        },
        "/upcoming_event_registrations": {
            "get": {
                "summary": "Админский метод - список записавшихся на событие",
                "description": "Retrieves a list of upcoming event registrations",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    }
                ],
                "responses": {
                    "200": {"description": "List of upcoming event registrations"}
                }
            }
        },
        "/users/office/{telegram_id}": {
            "get": {
                "summary": "Получить инфу какой любимый офис у пользователя",
                "description": "Retrieves the user's preferred office",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    },
                    {
                        "name": "telegram_id",
                        "in": "path",
                        "type": "integer",
                        "required": True,
                        "description": "Telegram ID of the user"
                    }
                ],
                "responses": {
                    "200": {"description": "User office information"},
                    "404": {"description": "User or office not found"}
                }
            },
            "put": {
                "summary": "Обновить любимый офис у пользователя",
                "description": "Updates the user's preferred office",
                "parameters": [
                    {
                        "name": "X-API-KEY",
                        "in": "header",
                        "type": "string",
                        "required": True,
                        "description": "API key"
                    },
                    {
                        "name": "telegram_id",
                        "in": "path",
                        "type": "integer",
                        "required": True,
                        "description": "Telegram ID of the user"
                    },
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "office_id": {"type": "integer"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "User office updated successfully"},
                    "404": {"description": "User not found"},
                    "400": {"description": "Invalid office ID format"},
                    "500": {"description": "Internal Server Error"}
                }
            }
        }
    }
}