### Healthcare

Healthcare

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app healthcare
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/healthcare
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

<img src="https://github.com/usmantiberbu/Capstone-project-healthcare/blob/main/screenshoots/15852b39-ea31-4b83-8872-c42d83db3f0f.jpeg">
<img src="https://github.com/usmantiberbu/Capstone-project-healthcare/blob/main/screenshoots/a0c3c420-efa2-4d05-a3fc-b94b484b185b.jpeg">
<img src="https://github.com/usmantiberbu/Capstone-project-healthcare/blob/main/screenshoots/c66003f8-668f-4621-a965-051b94959916.jpeg">
<img src="https://github.com/usmantiberbu/Capstone-project-healthcare/blob/main/screenshoots/645a4470-cdaf-4ee0-a26c-a3493b2f350e.jpeg">

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
