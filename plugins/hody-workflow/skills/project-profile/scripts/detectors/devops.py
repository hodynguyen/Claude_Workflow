"""Detect CI/CD, containerization, and infrastructure."""
import os


def detect_devops(cwd):
    """Detect CI/CD, containerization, and infrastructure."""
    devops = {}

    # Container
    if os.path.isfile(os.path.join(cwd, "Dockerfile")):
        devops["containerize"] = "docker"
    elif os.path.isfile(os.path.join(cwd, "docker-compose.yml")) or os.path.isfile(
        os.path.join(cwd, "docker-compose.yaml")
    ):
        devops["containerize"] = "docker"

    # CI
    if os.path.isdir(os.path.join(cwd, ".github", "workflows")):
        devops["ci"] = "github-actions"
    elif os.path.isfile(os.path.join(cwd, ".gitlab-ci.yml")):
        devops["ci"] = "gitlab-ci"
    elif os.path.isfile(os.path.join(cwd, "Jenkinsfile")):
        devops["ci"] = "jenkins"

    # Infrastructure
    tf_files = [f for f in os.listdir(cwd) if f.endswith(".tf")] if os.path.isdir(cwd) else []
    if tf_files:
        devops["infra"] = "terraform"
    elif os.path.isdir(os.path.join(cwd, "pulumi")):
        devops["infra"] = "pulumi"

    return devops if devops else None
