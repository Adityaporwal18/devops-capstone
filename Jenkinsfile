pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 40, unit: 'MINUTES')
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        IMAGE = 'adityaporwal18/eventhub'
        KUBECTL = 'sudo -H -u aditya kubectl --context capstone'
        CI_PROJECT = "eventhub-ci-${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                    env.DEPLOY_COMMIT = sh(returnStdout: true, script: "git log -1 --pretty=%s | grep -c 'skip ci' || true").trim()
                    env.APP_VERSION = sh(returnStdout: true, script: '. ./release.env && echo $APP_VERSION').trim()
                    env.FAULT_RATE = sh(returnStdout: true, script: '. ./release.env && echo $FAULT_RATE').trim()
                }
                sh 'mkdir -p reports && echo "Release $APP_VERSION, commit $GIT_SHA"'
            }
        }

        stage('Release pipeline') {
            when {
                expression { env.DEPLOY_COMMIT == '0' }
            }
            stages {
                stage('Unit tests') {
                    steps {
                        sh 'docker build -q --target test -t eventhub-test:$GIT_SHA .'
                        sh 'docker run --rm eventhub-test:$GIT_SHA pytest -v tests/test_rules.py'
                    }
                }

                stage('Integration tests') {
                    steps {
                        sh 'docker compose -p $CI_PROJECT -f compose.test.yml run --rm --build --quiet-pull tests'
                    }
                    post {
                        always {
                            sh 'docker compose -p $CI_PROJECT -f compose.test.yml down -v --rmi local'
                        }
                    }
                }

                stage('Static analysis') {
                    steps {
                        sh '''
                            docker run --rm eventhub-test:$GIT_SHA bandit -r app wsgi.py gunicorn.conf.py -f txt > reports/bandit.txt || true
                            cat reports/bandit.txt
                            echo "Gate: the build fails on any HIGH severity finding"
                            docker run --rm eventhub-test:$GIT_SHA bandit -r app wsgi.py gunicorn.conf.py -lll -q
                        '''
                    }
                }

                stage('Dependency audit') {
                    steps {
                        sh '''
                            status=0
                            docker run --rm eventhub-test:$GIT_SHA pip-audit -r requirements.txt > reports/pip-audit.txt 2>&1 || status=$?
                            cat reports/pip-audit.txt
                            exit $status
                        '''
                    }
                }

                stage('Build image') {
                    steps {
                        sh '''
                            docker build -q --target runtime \
                                --build-arg APP_VERSION=$APP_VERSION --build-arg GIT_SHA=$GIT_SHA --build-arg FAULT_RATE=$FAULT_RATE \
                                -t $IMAGE:$GIT_SHA .
                            docker images $IMAGE
                        '''
                    }
                }

                stage('Image scan') {
                    steps {
                        sh '''
                            trivy image --no-progress --severity HIGH,CRITICAL --ignore-unfixed --format table --output reports/trivy.txt $IMAGE:$GIT_SHA
                            grep -E "Total:|^Python|\\(debian" reports/trivy.txt || true
                            echo "Gate: the build fails on CRITICAL vulnerabilities that have a fix"
                            trivy image --no-progress --quiet --severity CRITICAL --ignore-unfixed --exit-code 1 $IMAGE:$GIT_SHA
                        '''
                    }
                }

                stage('Push image') {
                    steps {
                        sh 'docker push -q $IMAGE:$GIT_SHA'
                    }
                }

                stage('Deploy canary') {
                    steps {
                        withCredentials([sshUserPrivateKey(credentialsId: 'eventhub-gitops-key', keyFileVariable: 'GITOPS_KEY')]) {
                            script {
                                env.CANARY_REVISION = sh(returnStdout: true, script: 'scripts/gitops.sh canary $GIT_SHA').trim()
                            }
                        }
                        script {
                            env.CANARY_DEPLOYED = 'true'
                        }
                        sh 'scripts/wait-rollout.sh $CANARY_REVISION eventhub-canary'
                        sh '$KUBECTL -n eventhub get pods -L track'
                    }
                }

                stage('Canary analysis') {
                    steps {
                        sh 'scripts/canary-check.sh 300'
                    }
                }

                stage('Promote') {
                    steps {
                        withCredentials([sshUserPrivateKey(credentialsId: 'eventhub-gitops-key', keyFileVariable: 'GITOPS_KEY')]) {
                            script {
                                env.STABLE_REVISION = sh(returnStdout: true, script: 'scripts/gitops.sh promote $GIT_SHA').trim()
                            }
                        }
                        script {
                            env.PROMOTED = 'true'
                        }
                        sh 'scripts/wait-rollout.sh $STABLE_REVISION eventhub-stable eventhub-canary'
                        sh '$KUBECTL -n eventhub get deployments -o wide'
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                if (env.PROMOTED == 'true') {
                    echo "Release ${env.APP_VERSION} (${env.GIT_SHA}) passed the canary analysis and is now the stable version."
                } else {
                    echo 'Deployment commit made by the pipeline: nothing to build.'
                }
            }
        }
        failure {
            script {
                if (env.CANARY_DEPLOYED == 'true' && env.PROMOTED != 'true') {
                    echo 'The canary did not pass: rolling it back automatically.'
                    withCredentials([sshUserPrivateKey(credentialsId: 'eventhub-gitops-key', keyFileVariable: 'GITOPS_KEY')]) {
                        env.ROLLBACK_REVISION = sh(returnStdout: true, script: 'scripts/gitops.sh rollback $GIT_SHA').trim()
                    }
                    sh 'scripts/wait-rollout.sh $ROLLBACK_REVISION eventhub-canary'
                    sh '$KUBECTL -n eventhub get deployments -o wide'
                    echo 'Rollback finished: all traffic is served by the previous stable version.'
                } else {
                    echo 'The pipeline stopped before deployment: the running version is unchanged.'
                }
            }
        }
        always {
            archiveArtifacts artifacts: 'reports/*', allowEmptyArchive: true
            sh 'docker rmi -f eventhub-test:$GIT_SHA > /dev/null 2>&1 || true'
        }
    }
}
