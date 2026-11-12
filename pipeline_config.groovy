// Config JTE cho devops-lab: chỉ khai báo template + tham số.
// Template và step nằm ở repo pipeline-config / pipeline-lib.
pipeline_template = 'python-docker-ci'

libraries {
    lib {
        // unit_test
        python_version = '3.12'
        requirements   = 'requirements/dev.txt'

        // build / push: tạo image registry:5000/devops-lab-<target>:<BUILD_NUMBER>
        registry = 'registry:5000'
        image    = 'devops-lab'
        targets  = ['api', 'app']          // 2 stage trong Dockerfile

        // deploy
        env_credentials_id = 'devops-lab-env'   // Secret file trong Jenkins (nội dung .env)
        compose_file       = 'docker-compose.yaml'
        compose_override   = 'deploy/docker-compose.ci.yaml'

        // smoke_test: api chạy trong dind -> gọi qua hostname docker
        health_url = 'http://docker:8081/healthz'
    }
}
