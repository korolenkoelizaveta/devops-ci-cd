pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

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

        stage('Prepare Release') {
            when {
                expression {
                    env.GIT_BRANCH == 'origin/main'
                }
            }

            steps {
                echo 'Подготовка стабильной версии приложения'

                bat '''
                    if exist release rmdir /S /Q release
                    mkdir release

                    xcopy app release\\app /E /I /Y
                    xcopy gym release\\gym /E /I /Y
                    xcopy client\\dist release\\client\\dist /E /I /Y

                    copy manage.py release\\
                    copy requirements.txt release\\

                    for /d /r release %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
                    del /S /Q release\\*.pyc 2>nul
                '''
            }
        }

        stage('Delivery') {
            when {
                expression {
                    env.GIT_BRANCH == 'origin/main'
                }
            }

            steps {
                echo 'Сохранение релизной версии в Jenkins'

                archiveArtifacts(
                    artifacts: 'release/**/*',
                    fingerprint: true
                )
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