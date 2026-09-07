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
                bat 'python -m pip install -r requirements.txt'
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

        stage('Tests') {
            steps {
                echo 'Запуск 20 CRUD-тестов'
                bat 'python manage.py test'
            }
        }

        stage('Build') {
            steps {
                echo 'Сборка Vue'
                dir('client') {
                    bat 'npm run build'
                }
            }
        }

        stage('Deploy') {
            when {
                expression {
                    env.GIT_BRANCH == 'origin/main'
                }
            }

            steps {
                echo 'Развертывание стабильной версии приложения'
            }
        }
    }

    post {
        success {
            echo 'Pipeline успешно завершен'
        }

        failure {
            echo 'Pipeline завершен с ошибкой'
        }
    }
}