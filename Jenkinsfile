pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Получение исходного кода из GitHub'
                checkout scm
            }
        }

        stage('Backend Dependencies') {
            steps {
                echo 'Установка зависимостей Django'
                bat 'py -m pip install -r requirements.txt'
            }
        }

        stage('Frontend Dependencies') {
            steps {
                echo 'Установка зависимостей Vue'
                dir('client') {
                    bat 'npm ci'
                }
            }
        }

        stage('Backend Tests') {
            steps {
                echo 'Запуск автоматических тестов Django'
                bat 'py manage.py test'
            }
        }

        stage('Frontend Build') {
            steps {
                echo 'Сборка Vue'
                dir('client') {
                    bat 'npm run build'
                }
            }
        }
    }

    post {
        success {
            echo 'CI pipeline успешно завершен'
        }

        failure {
            echo 'CI pipeline завершен с ошибкой'
        }
    }
}