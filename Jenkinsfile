pipeline {
    agent any

    environment {
        REGISTRY = 'registry.gitlab.com'
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    env.BRANCH_NAME = "${GIT_BRANCH.replaceFirst(/^.*\//, '')}"

                    // Determine the profile based on the branch
                    def profile = (env.BRANCH_NAME in ['master', 'main']) ? 'prod' :
                                  (env.BRANCH_NAME == 'staging') ? 'staging' :
                                  (env.BRANCH_NAME == 'dev') ? 'dev' :
                                  env.BRANCH_NAME

                    // Construct the image name
                    def imageName = "${env.REGISTRY}/khiemnd51/image-storage/pika-mem0-enterprise_${profile}:${env.BUILD_NUMBER}"

                    // Log the determined values
                    echo "Profile: ${profile}"
                    echo "Image Name: ${imageName}"

                    // Set environment variables
                    env.PROFILE = profile
                    env.IMAGE_NAME = imageName
                }
            }
        }

        stage('Checkout') {
            steps {
                script {
                    echo 'Checking out branch: ' + env.BRANCH_NAME + ' with profile: ' + env.PROFILE
                    checkout scm

                    def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    env.COMMIT_MESSAGE = commitMessage
                    echo "Commit Message: ${commitMessage}"

                    slackSend color: "#439FE0", message: "Build STARTED\nCommit: ${env.GIT_COMMIT}\nCommit Message: ${env.COMMIT_MESSAGE}\nBranch: ${env.BRANCH_NAME}\nBuild number: ${env.BUILD_NUMBER}\nImage name: ${env.IMAGE_NAME}"
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    sh """
                        docker build -t ${env.IMAGE_NAME} .
                    """
                }
            }
        }

        stage('Publish') {
            steps {
                withCredentials([string(credentialsId: 'gitlab_access_token', variable: 'TOKEN')]) {
                    script {
                        sh """
                            echo "${TOKEN}" | docker login ${env.REGISTRY} -u khiemnd51 --password-stdin
                            docker push ${env.IMAGE_NAME}
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            slackSend color: "good", message: "Build SUCCEEDED\nCommit: ${env.GIT_COMMIT}\nCommit Message: ${env.COMMIT_MESSAGE}\nBranch: ${env.BRANCH_NAME}\nBuild number: ${env.BUILD_NUMBER}\nImage name: ${env.IMAGE_NAME}"
        }

        failure {
            slackSend color: "danger", message: "Build FAILED\nCommit: ${env.GIT_COMMIT}\nCommit Message: ${env.COMMIT_MESSAGE}\nBranch: ${env.BRANCH_NAME}\nBuild number: ${env.BUILD_NUMBER}\nImage name: ${env.IMAGE_NAME}"
        }

        aborted {
            slackSend color: "warning", message: "Build ABORTED\nCommit: ${env.GIT_COMMIT}\nCommit Message: ${env.COMMIT_MESSAGE}\nBranch: ${env.BRANCH_NAME}\nBuild number: ${env.BUILD_NUMBER}\nImage name: ${env.IMAGE_NAME}"
        }
    }
}
