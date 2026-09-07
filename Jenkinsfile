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

        stage('Backend Tests') {
            steps {
                echo 'Запуск 20 CRUD-тестов Django'
                bat 'python manage.py test'
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

        stage('Promote to Main') {
            steps {
                echo 'Продвижение проверенной версии dev в main'

                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-push',
                        usernameVariable: 'GIT_USERNAME',
                        passwordVariable: 'GIT_TOKEN'
                    )
                ]) {
                    bat '''
                        @echo off
                        git push https://%GIT_USERNAME%:%GIT_TOKEN%@github.com/korolenkoelizaveta/devops-ci-cd.git HEAD:main
                    '''
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