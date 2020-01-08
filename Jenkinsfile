#!groovy

pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                echo 'Stage: Checkout...'
                checkout scm
            }
        }
        stage('Container build') {
            steps {
                echo 'Stage: Building...'
                sh "pipeline/build/build.sh"
            }
        }
        stage('Unittests') {
            steps {
                echo 'Stage: Testing...'
                sh "pipeline/unittest/test.sh"
            }
        }
        stage('Style check') {
            steps {
                echo 'Stage: Style check...'
                sh "pipeline/checkstyle/check.sh"
            }
        }
        stage('Smoke tests') {
            steps {
                echo 'Stage: Smoke test... (not implemented)'
            }
        }
        stage('Integration tests (SDK-tools)')
        {
            steps {
                echo 'Stage: Integration tests (SDK-tools)'
                // ensure that no old container is there
                sh "docker rm -f tng-sdk-project || true"
                sh "docker run --rm --name tng-sdk-project-int registry.sonata-nfv.eu:5000/tng-sdk-project pipeline/unittest/test_sdk_integration.sh"
            }
        }
        stage ("Downstream jobs: Trigger tng-sdk-package build") {
            when{
                branch 'master'
            }
            steps {
                build job: '../tng-sdk-package-pipeline/master', wait: true
            }
        }
        stage('Container publication') {
            steps {
                echo 'Stage: Container publication...'
				sh "pipeline/publish/publish.sh"
            }
        }
		// for release v5.0
		stage('Promoting release v5.1') {
        when {
            branch 'v5.1'
        }
        stages {
            stage('Generating release') {
                steps {
                    sh 'docker tag registry.sonata-nfv.eu:5000/tng-sdk-project:latest registry.sonata-nfv.eu:5000/tng-sdk-project:v5.1'
                    sh 'docker tag registry.sonata-nfv.eu:5000/tng-sdk-project:latest sonatanfv/tng-sdk-project:v5.1'
                    sh 'docker push registry.sonata-nfv.eu:5000/tng-sdk-project:v5.1'
                    sh 'docker push sonatanfv/tng-sdk-project:v5.1'
                }
            }
        }
    }

    }
    post {
         success {
                 emailext(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "SUCCESS: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
         failure {
                 emailext(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "FAILURE: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
    }
}
