"""Tests for detect_stack.py using mock project structures."""
import json
import os
import sys
import tempfile
import unittest

# Add the script to path
SCRIPT_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "plugins",
    "hody-workflow",
    "skills",
    "project-profile",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

from detect_stack import build_profile, to_yaml


class TestEmptyProject(unittest.TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "unknown")
            self.assertNotIn("frontend", profile)
            self.assertNotIn("backend", profile)


class TestNodeProject(unittest.TestCase):
    def _make_package_json(self, tmpdir, deps=None, dev_deps=None):
        pkg = {"name": "test-app", "dependencies": deps or {}, "devDependencies": dev_deps or {}}
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            json.dump(pkg, f)

    def test_react_frontend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0", "react-dom": "^18.0.0"},
                dev_deps={"typescript": "^5.0.0", "vitest": "^1.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "frontend")
            self.assertEqual(profile["frontend"]["framework"], "react")
            self.assertEqual(profile["frontend"]["language"], "typescript")
            self.assertEqual(profile["frontend"]["testing"], "vitest")

    def test_next_overrides_react(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0", "next": "^14.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["framework"], "next")

    def test_vue_frontend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(tmpdir, deps={"vue": "^3.0.0"})
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["framework"], "vue")

    def test_express_backend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"express": "^4.18.0", "@prisma/client": "^5.0.0"},
                dev_deps={"prisma": "^5.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["framework"], "express")
            self.assertEqual(profile["backend"]["orm"], "prisma")

    def test_fullstack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0", "fastify": "^4.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "fullstack")
            self.assertEqual(profile["frontend"]["framework"], "react")
            self.assertEqual(profile["backend"]["framework"], "fastify")

    def test_state_management(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(tmpdir, deps={"react": "^18.0.0", "zustand": "^4.0.0"})
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["state"], "zustand")

    def test_styling_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0"},
                dev_deps={"tailwindcss": "^3.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["styling"], "tailwind")

    def test_conventions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0"},
                dev_deps={"eslint": "^8.0.0", "prettier": "^3.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["conventions"]["linter"], "eslint")
            self.assertEqual(profile["conventions"]["formatter"], "prettier")


class TestGoProject(unittest.TestCase):
    def test_gin_backend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "go.mod"), "w") as f:
                f.write("module github.com/test/api\n\nrequire github.com/gin-gonic/gin v1.9.1\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "go")
            self.assertEqual(profile["backend"]["framework"], "gin")
            self.assertEqual(profile["backend"]["testing"], "go-test")

    def test_echo_with_gorm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "go.mod"), "w") as f:
                f.write("module test\n\nrequire (\n  github.com/labstack/echo v4\n  gorm.io/gorm v1.25\n)\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "echo")
            self.assertEqual(profile["backend"]["orm"], "gorm")


class TestPythonProject(unittest.TestCase):
    def test_fastapi(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write("fastapi==0.104.0\nsqlalchemy==2.0.0\npytest==7.4.0\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "python")
            self.assertEqual(profile["backend"]["framework"], "fastapi")
            self.assertEqual(profile["backend"]["orm"], "sqlalchemy")
            self.assertEqual(profile["backend"]["testing"], "pytest")

    def test_django(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write("django==4.2.0\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "django")
            self.assertEqual(profile["backend"]["orm"], "django-orm")


class TestRustProject(unittest.TestCase):
    def test_actix_web(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "Cargo.toml"), "w") as f:
                f.write('[dependencies]\nactix-web = "4"\nsqlx = { version = "0.7" }\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "rust")
            self.assertEqual(profile["backend"]["framework"], "actix-web")
            self.assertEqual(profile["backend"]["orm"], "sqlx")
            self.assertEqual(profile["backend"]["testing"], "cargo-test")

    def test_axum(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "Cargo.toml"), "w") as f:
                f.write('[dependencies]\naxum = "0.7"\nstatic diesel = "2"\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "axum")
            self.assertEqual(profile["backend"]["orm"], "diesel")

    def test_rocket(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "Cargo.toml"), "w") as f:
                f.write('[dependencies]\nrocket = "0.5"\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "rocket")


class TestJavaProject(unittest.TestCase):
    def test_spring_boot_maven(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "pom.xml"), "w") as f:
                f.write('<project>\n<parent>\n<artifactId>spring-boot-starter-parent</artifactId>\n</parent>\n</project>\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "java")
            self.assertEqual(profile["backend"]["framework"], "spring-boot")
            self.assertEqual(profile["backend"]["build"], "maven")
            self.assertEqual(profile["backend"]["testing"], "junit")

    def test_spring_boot_gradle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "build.gradle"), "w") as f:
                f.write("plugins {\n  id 'org.springframework.boot' version '3.2.0'\n}\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "spring-boot")
            self.assertEqual(profile["backend"]["build"], "gradle")

    def test_kotlin_spring(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "build.gradle.kts"), "w") as f:
                f.write('plugins {\n  kotlin("jvm")\n  id("org.springframework.boot")\n}\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["language"], "kotlin")
            self.assertEqual(profile["backend"]["framework"], "spring-boot")

    def test_quarkus(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "pom.xml"), "w") as f:
                f.write('<project>\n<dependency>\n<groupId>io.quarkus</groupId>\n</dependency>\n</project>\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "quarkus")


class TestNodeAdditional(unittest.TestCase):
    def _make_package_json(self, tmpdir, deps=None, dev_deps=None):
        pkg = {"name": "test-app", "dependencies": deps or {}, "devDependencies": dev_deps or {}}
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            json.dump(pkg, f)

    def test_angular(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(tmpdir, deps={"@angular/core": "^17.0.0"})
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["framework"], "angular")

    def test_svelte(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(tmpdir, deps={"svelte": "^4.0.0"})
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["framework"], "svelte")

    def test_sveltekit_overrides_svelte(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"svelte": "^4.0.0"},
                dev_deps={"@sveltejs/kit": "^2.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["framework"], "sveltekit")

    def test_nest_backend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"@nestjs/core": "^10.0.0"},
                dev_deps={"typescript": "^5.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["framework"], "nest")
            self.assertEqual(profile["backend"]["language"], "typescript")


class TestDevOps(unittest.TestCase):
    def test_docker(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "Dockerfile"), "w").close()
            profile = build_profile(tmpdir)
            self.assertEqual(profile["devops"]["containerize"], "docker")

    def test_github_actions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".github", "workflows"))
            profile = build_profile(tmpdir)
            self.assertEqual(profile["devops"]["ci"], "github-actions")

    def test_gitlab_ci(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, ".gitlab-ci.yml"), "w").close()
            profile = build_profile(tmpdir)
            self.assertEqual(profile["devops"]["ci"], "gitlab-ci")

    def test_database_from_env(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env.example"), "w") as f:
                f.write("DATABASE_URL=postgresql://localhost:5432/mydb\n")
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write("fastapi==0.104.0\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["database"], "postgresql")


class TestCSharpProject(unittest.TestCase):
    def test_aspnet_core(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "MyApp.csproj"), "w") as f:
                f.write('<Project Sdk="Microsoft.NET.Sdk.Web">\n<PackageReference Include="Microsoft.AspNetCore" />\n<PackageReference Include="Microsoft.EntityFrameworkCore" />\n<PackageReference Include="xunit" />\n</Project>\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "csharp")
            self.assertEqual(profile["backend"]["framework"], "aspnet-core")
            self.assertEqual(profile["backend"]["orm"], "entity-framework")
            self.assertEqual(profile["backend"]["testing"], "xunit")

    def test_blazor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "App.csproj"), "w") as f:
                f.write('<Project Sdk="Microsoft.NET.Sdk.Blazor">\n<PackageReference Include="nunit" />\n</Project>\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "blazor")
            self.assertEqual(profile["backend"]["testing"], "nunit")

    def test_dotnet_sln_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "MyApp.sln"), "w") as f:
                f.write("Microsoft Visual Studio Solution File\n")
            with open(os.path.join(tmpdir, "MyApp.csproj"), "w") as f:
                f.write('<Project Sdk="Microsoft.NET.Sdk">\n</Project>\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["language"], "csharp")
            self.assertEqual(profile["backend"]["framework"], "dotnet")

    def test_dapper_orm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "Api.csproj"), "w") as f:
                f.write('<Project>\n<PackageReference Include="Microsoft.AspNetCore" />\n<PackageReference Include="Dapper" />\n<PackageReference Include="MSTest" />\n</Project>\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["orm"], "dapper")
            self.assertEqual(profile["backend"]["testing"], "mstest")


class TestRubyProject(unittest.TestCase):
    def test_rails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "Gemfile"), "w") as f:
                f.write("source 'https://rubygems.org'\ngem 'rails', '~> 7.1'\ngem 'rspec-rails'\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "ruby")
            self.assertEqual(profile["backend"]["framework"], "rails")
            self.assertEqual(profile["backend"]["orm"], "activerecord")
            self.assertEqual(profile["backend"]["testing"], "rspec")

    def test_sinatra(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "Gemfile"), "w") as f:
                f.write("gem 'sinatra'\ngem 'sequel'\ngem 'minitest'\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "sinatra")
            self.assertEqual(profile["backend"]["orm"], "sequel")
            self.assertEqual(profile["backend"]["testing"], "minitest")

    def test_hanami(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "Gemfile"), "w") as f:
                f.write("gem 'hanami', '~> 2.1'\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "hanami")


class TestPHPProject(unittest.TestCase):
    def test_laravel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = {
                "require": {"laravel/framework": "^10.0"},
                "require-dev": {"phpunit/phpunit": "^10.0"},
            }
            with open(os.path.join(tmpdir, "composer.json"), "w") as f:
                json.dump(composer, f)
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "php")
            self.assertEqual(profile["backend"]["framework"], "laravel")
            self.assertEqual(profile["backend"]["orm"], "eloquent")
            self.assertEqual(profile["backend"]["testing"], "phpunit")

    def test_symfony(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = {
                "require": {"symfony/framework-bundle": "^6.0", "doctrine/orm": "^2.0"},
                "require-dev": {"pestphp/pest": "^2.0"},
            }
            with open(os.path.join(tmpdir, "composer.json"), "w") as f:
                json.dump(composer, f)
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "symfony")
            self.assertEqual(profile["backend"]["orm"], "doctrine")
            self.assertEqual(profile["backend"]["testing"], "pest")

    def test_magento(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = {"require": {"magento/product-community-edition": "2.4.6"}}
            with open(os.path.join(tmpdir, "composer.json"), "w") as f:
                json.dump(composer, f)
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "magento")


class TestMonorepoDetection(unittest.TestCase):
    def test_turborepo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "turbo.json"), "w") as f:
                f.write('{"$schema": "https://turbo.build/schema.json"}\n')
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump({"name": "monorepo", "workspaces": ["packages/*"]}, f)
            # Create a workspace package
            pkg_dir = os.path.join(tmpdir, "packages", "web")
            os.makedirs(pkg_dir)
            with open(os.path.join(pkg_dir, "package.json"), "w") as f:
                json.dump({"name": "web", "dependencies": {"react": "^18.0.0"}}, f)
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "monorepo")
            self.assertEqual(profile["monorepo"]["tool"], "turborepo")
            self.assertEqual(len(profile["monorepo"]["workspaces"]), 1)
            self.assertEqual(profile["monorepo"]["workspaces"][0]["framework"], "react")

    def test_nx(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "nx.json"), "w") as f:
                f.write("{}\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "monorepo")
            self.assertEqual(profile["monorepo"]["tool"], "nx")

    def test_lerna(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "lerna.json"), "w") as f:
                f.write('{"version": "0.0.0"}\n')
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "monorepo")
            self.assertEqual(profile["monorepo"]["tool"], "lerna")

    def test_pnpm_workspaces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "pnpm-workspace.yaml"), "w") as f:
                f.write("packages:\n  - 'apps/*'\n")
            # Create a workspace
            app_dir = os.path.join(tmpdir, "apps", "api")
            os.makedirs(app_dir)
            with open(os.path.join(app_dir, "requirements.txt"), "w") as f:
                f.write("fastapi==0.104.0\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "monorepo")
            self.assertEqual(profile["monorepo"]["tool"], "pnpm-workspaces")
            self.assertEqual(len(profile["monorepo"]["workspaces"]), 1)
            self.assertEqual(profile["monorepo"]["workspaces"][0]["language"], "python")
            self.assertEqual(profile["monorepo"]["workspaces"][0]["framework"], "fastapi")

    def test_turborepo_multiple_workspaces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "turbo.json"), "w") as f:
                f.write("{}\n")
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump({"name": "mono", "workspaces": ["packages/*"]}, f)
            # Frontend workspace
            fe_dir = os.path.join(tmpdir, "packages", "frontend")
            os.makedirs(fe_dir)
            with open(os.path.join(fe_dir, "package.json"), "w") as f:
                json.dump({"name": "frontend", "dependencies": {"vue": "^3.0.0"}}, f)
            # Backend workspace
            be_dir = os.path.join(tmpdir, "packages", "api")
            os.makedirs(be_dir)
            with open(os.path.join(be_dir, "go.mod"), "w") as f:
                f.write("module api\n\nrequire github.com/gin-gonic/gin v1.9\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "monorepo")
            self.assertEqual(len(profile["monorepo"]["workspaces"]), 2)
            frameworks = {ws["framework"] for ws in profile["monorepo"]["workspaces"] if "framework" in ws}
            self.assertIn("vue", frameworks)
            self.assertIn("gin", frameworks)


class TestToYaml(unittest.TestCase):
    def test_simple_dict(self):
        result = to_yaml({"key": "value"})
        self.assertEqual(result, "key: value")

    def test_nested_dict(self):
        result = to_yaml({"parent": {"child": "value"}})
        self.assertIn("parent:", result)
        self.assertIn("  child: value", result)

    def test_boolean(self):
        result = to_yaml({"flag": True})
        self.assertEqual(result, "flag: true")

    def test_list(self):
        result = to_yaml({"items": [{"name": "a", "value": "1"}, {"name": "b", "value": "2"}]})
        self.assertIn("items:", result)
        self.assertIn("  - name: a", result)
        self.assertIn("    value: 1", result)


if __name__ == "__main__":
    unittest.main()
