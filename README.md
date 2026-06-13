# SkillSprint

SkillSprint is a CS50W capstone web application built with Django and JavaScript. It is a mobile-responsive learning planner that helps a user turn a broad learning goal into milestones, scheduled practice sessions, and progress notes. The app includes authenticated pages, private user-owned records, CRUD workflows, dashboard summaries, search and filtering, progressive JavaScript enhancements, JWT-backed API endpoints, automated tests, and deployment scaffolding.

The application is intended for students, self-learners, and professionals who want a structured way to manage skill-building work. A user can create a goal such as learning Django forms, break that goal into ordered milestones, schedule practice sessions, mark work as complete or skipped, and write notes about what they learned. The dashboard summarizes active goals, upcoming sessions, overdue milestones, recent notes, and completion progress.

## Distinctiveness and Complexity

SkillSprint is distinct from the other CS50W projects because it is not a social network, e-commerce site, email client, encyclopedia, or pizza-ordering application. Its purpose is private learning planning and progress tracking. The central workflow is not posting public content, buying products, sending messages, or editing reference entries; it is managing personal learning plans through connected goals, milestones, sessions, and notes.

This project is different from a social network because users will not follow each other, publish feeds, like posts, send messages, or browse other users' content. Every major record belongs to one authenticated user, and the application must protect that user's learning data on every page, form action, and API endpoint. The main interaction is between the learner and their own plan.

It is also different from an e-commerce project because there are no products, carts, payments, inventories, shipments, or orders. Although SkillSprint will include list, detail, create, edit, and delete pages, those pages represent private learning records rather than items for sale. The complexity comes from planning, scheduling, validation, progress calculation, and ownership boundaries.

SkillSprint is complex enough for the capstone because it requires several related Django models and meaningful backend behavior. A `Goal` contains ordered `Milestone` records, scheduled `PracticeSession` records, and `ProgressNote` records. A practice session belongs to a user and goal, and may optionally connect to a milestone. A progress note belongs to a user and goal, and may optionally connect to a milestone or session. These relationships require validation so that a session or note cannot be attached to a milestone from the wrong goal or to records owned by another user.

The dashboard and progress behavior add another layer of complexity. The app must calculate completion percentages, count upcoming sessions, find overdue milestones, show recent notes, and keep those summaries scoped to the logged-in user. JavaScript will progressively enhance common actions such as toggling a milestone, updating a session status, filtering dashboard content, and refreshing progress data, while Django remains the source of truth for validation, permissions, and persistence.

The project will also be mobile-responsive. Dashboard panels, navigation, forms, buttons, cards, lists, and tables must adapt to desktop, tablet, and phone widths. The interface should feel calm and useful for repeated study planning rather than like a marketing page.

## Features

- User registration, login, and logout.
- Private goals owned by each authenticated user.
- CRUD pages for goals, milestones, practice sessions, and progress notes.
- Ordered milestones inside each goal.
- Practice sessions connected to goals and optional milestones.
- Progress notes connected to goals and optional milestones or sessions.
- Dashboard with active goals, upcoming sessions, overdue milestones, recent notes, and completion summaries.
- Search and filtering for goals, practice sessions, progress notes, and dashboard content.
- JavaScript-powered milestone toggles, session status updates, filtering, and progress refreshes.
- JWT-backed `/api/` endpoints using a consistent JSON response format.
- Responsive HTML and CSS for desktop and mobile use.

## Technology

The stack is Python 3.12, Django 5.2 LTS, Django REST Framework 3.16, `djangorestframework-simplejwt` 5.5, SQLite for local capstone development, optional PostgreSQL-compatible production database configuration through `DATABASE_URL`, server-rendered Django templates, vanilla JavaScript, and CSS. Gunicorn is included for container runtime serving.

Rendered pages will use Django session authentication. JSON endpoints under `/api/` will use JWT authentication. This hybrid approach keeps the project aligned with Django's strengths while still demonstrating API authentication and JavaScript interaction.

Cloudflare is the planned production edge direction. The repository includes a Dockerfile, Cloudflare Containers Worker scaffold, `wrangler.toml`, and a manual GitHub Actions deploy workflow. A real deployment still requires a Cloudflare paid Workers account, production route, secrets, and managed database URL. SQLite is acceptable for local development and capstone submission, but any real production deployment should use a PostgreSQL-compatible managed database rather than a SQLite file inside a container.

## Project Structure

```text
Capstone/
  README.md
  FEATURE_SPEC.md
  Note.txt
  .gitignore
  requirements.txt
  package.json
  Dockerfile
  .dockerignore
  wrangler.toml
  manage.py
  capstone/
    __init__.py
    asgi.py
    settings.py
    urls.py
    wsgi.py
  planner/
    __init__.py
    admin.py
    apps.py
    forms.py
    models.py
    urls.py
    views.py
    services.py
    tests/
      __init__.py
      test_api.py
      test_auth.py
      test_dashboard.py
      test_goals.py
      test_milestones.py
      test_models.py
      test_progress_notes.py
      test_sessions.py
      test_setup.py
    templates/
      planner/
        base.html
        landing.html
        dashboard.html
        goal_list.html
        goal_detail.html
        goal_form.html
        goal_confirm_delete.html
        milestone_form.html
        session_list.html
        session_form.html
        progress_log.html
        progress_note_form.html
        progress_note_confirm_delete.html
        session_confirm_delete.html
        milestone_confirm_delete.html
        auth/
          login.html
          register.html
    static/
      planner/
        css/
          styles.css
        js/
          api.js
          dashboard.js
          goal_detail.js
  cloudflare/
    worker.js
  .github/
    workflows/
      ci.yml
      deploy.yml
```

## File Descriptions

`requirements.txt` pins Python dependencies for Django, Django REST Framework, Simple JWT, database URL parsing, PostgreSQL support, and Gunicorn. `package.json` pins the Cloudflare Worker deployment tooling. `.gitignore` keeps local virtual environments, caches, local databases, static build output, media files, and secrets out of version control. `manage.py` is the Django command-line entry point. The `capstone/` package contains project settings, root URLs, and WSGI/ASGI entry points. The `planner/` app contains the learning-planner domain code.

Inside `planner/`, `models.py` defines `Goal`, `Milestone`, `PracticeSession`, and `ProgressNote`. `forms.py` validates HTML form input and protects cross-object relationships. `views.py` contains page views and API views, with all queries scoped to the current user. `api.py` centralizes global JSON response helpers. `serializers.py` handles API auth serializers and token payloads. `services.py` holds shared dashboard, progress, and query helpers. `urls.py` defines app routes. `admin.py` registers models for Django admin inspection.

The `planner/tests/` package splits tests by behavior: setup, authentication, models, goals, milestones, sessions, progress notes, dashboard behavior, and API responses. Templates in `planner/templates/planner/` render the landing page, dashboard, goal pages, milestone forms, session pages, progress note pages, delete confirmations, and authentication pages. Static assets in `planner/static/planner/` contain one shared stylesheet and focused JavaScript files for API helpers, dashboard behavior, and goal detail behavior.

Deployment-related files include `Dockerfile` for a Gunicorn-backed Django image, `.dockerignore` to keep local-only files and secrets out of builds, `cloudflare/worker.js` and `wrangler.toml` for Cloudflare Containers routing, `.github/workflows/ci.yml` for automated checks, and `.github/workflows/deploy.yml` for a manual Cloudflare deployment after production secrets and routes are configured.

## How to Run

Use Python 3.12.x for the capstone runtime when available, and confirm the selected interpreter before creating the environment:

```bash
python3 --version
```

On macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Then run the initial migrations and start the development server:

```bash
python3 manage.py migrate
python3 manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

If an admin account is needed after migrations exist, run:

```bash
python3 manage.py createsuperuser
```

To build the Django container after Docker can pull the base image:

```bash
docker build -t skillsprint .
```

## Testing

The project includes Django tests for model creation, model relationships, progress calculations, authentication redirects, CRUD behavior, permission boundaries, invalid form submissions, JSON response shapes, JWT-authenticated endpoints, and ownership checks between two different users. Run:

```bash
python3 manage.py check
python3 manage.py test
```

The API tests confirm the global response shape:

```json
{
  "ok": true,
  "message": "Human-readable message.",
  "data": {}
}
```

Error responses should use:

```json
{
  "ok": false,
  "message": "Human-readable error message.",
  "errors": {}
}
```

Manual testing should cover the main end-to-end workflows: a new user creates a learning plan, a user completes a milestone from the goal detail page, a user updates a session from the dashboard, a second user cannot access another user's records, search and filters return only the current user's data, and the main pages remain usable on mobile screen sizes.

## Security and Data Ownership

SkillSprint stores private learning data, so user ownership is a core requirement. Every queryset must be scoped by `request.user` or a user-owned parent object before records are read, updated, or deleted. Hidden form fields and browser-submitted object IDs must not be trusted. If an object belongs to another user, the app should reject access without leaking private data.

Server-side validation is the source of truth. Django forms, model validation, and DRF serializers must reject invalid relationships such as connecting a session to a milestone from another goal. JavaScript may make the interface smoother, but it must not replace backend authorization or validation.

Production settings should use environment variables for secrets, debug mode, allowed hosts, CSRF trusted origins, database configuration, and Cloudflare credentials. Production should run with `DEBUG=False`, HTTPS, secure cookies, HTTP-only session cookies, pinned dependencies, refresh token rotation, and refresh token blacklisting on logout.

## Additional Information

The local final review passed `python manage.py check`, `python manage.py check --deploy` with production-style environment variables, `python manage.py test`, `python manage.py migrate --noinput` against a clean SQLite database, and `python manage.py collectstatic --noinput`. Dockerfile verification was attempted, but the local Docker registry pull stalled while downloading the base image; the app-level collectstatic step used by the Dockerfile was verified separately.

Cloudflare deployment files are included as scaffolding. Before a real deployment, configure the production route in `wrangler.toml`, add GitHub Actions secrets for `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, and `DATABASE_URL`, and confirm the Cloudflare zone SSL/TLS, WAF, caching, and managed database settings.
