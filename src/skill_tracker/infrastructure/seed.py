"""Optional demo data, inserted once into an empty database."""

from __future__ import annotations

from ..application.services import UnitOfWorkFactory
from ..application.unit_of_work import UnitOfWork
from ..domain.entities import Project, StudyLog, Topic


def seed_if_empty(uow_factory: UnitOfWorkFactory) -> None:
    with uow_factory() as uow:
        if uow.topics.list():
            return
        _seed(uow)


def _seed(uow: UnitOfWork) -> None:
    architecture = Topic.create(
        "System Architecture & Scalability",
        category="Engineering",
        color="blue",
        description=(
            "Mastering distributed systems, caching strategies, load balancing, "
            "and microservices design."
        ),
        notes="Key takeaway: always design for failure. Match caching to read/write ratios.",
        topic_id="t1",
    )
    for module_id, title, completed in [
        ("m1", "Load Balancing & Reverse Proxies", True),
        ("m2", "Database Sharding & Replication", True),
        ("m3", "Distributed Caching (Redis/Memcached)", False),
        ("m4", "Message Queues (Kafka/RabbitMQ)", False),
    ]:
        module = architecture.add_module(title, module_id=module_id)
        module.completed = completed

    machine_learning = Topic.create(
        "Machine Learning & PyTorch",
        category="AI / Data",
        color="purple",
        description="Deep dive into neural networks, computer vision, and NLP fine-tuning.",
        notes="AdamW is usually preferred for Transformers.",
        topic_id="t2",
    )
    for module_id, title, completed in [
        ("m201", "Tensors & Autograd Mechanics", True),
        ("m202", "Convolutional Neural Networks (CNNs)", True),
        ("m203", "Transformer Architecture Basics", True),
        ("m204", "Fine-Tuning LLaMA / HuggingFace", False),
    ]:
        module = machine_learning.add_module(title, module_id=module_id)
        module.completed = completed

    design = Topic.create(
        "Modern UI/UX & Micro-interactions",
        category="Design",
        color="emerald",
        description="Building accessible, high-performance web interfaces with motion design.",
        notes="Accessibility is not an afterthought; check contrast early.",
        topic_id="t3",
    )
    for module_id, title, completed in [
        ("m301", "Design Tokens & Color Systems", True),
        ("m302", "Framer Motion & Layout Animations", True),
        ("m303", "WCAG 2.1 AAA Accessibility Rules", False),
    ]:
        module = design.add_module(title, module_id=module_id)
        module.completed = completed

    topics = [architecture, machine_learning, design]
    for topic in topics:
        uow.topics.add(topic)

    projects = [
        Project.create(
            "Distributed Log Aggregator",
            topic_id="t1",
            status="Active",
            target_date="2026-12-15",
            hours_spent=28,
            repo_url="https://github.com/example/log-aggregator",
            tech_stack=["Go", "Kafka", "Elasticsearch", "Docker"],
            description=(
                "High-throughput real-time log ingestion pipeline supporting 10k logs/sec."
            ),
            project_id="p1",
        ),
        Project.create(
            "AI Code Review Assistant",
            topic_id="t2",
            status="Planning",
            target_date="2027-01-30",
            hours_spent=12,
            repo_url="https://github.com/example/ai-code-reviewer",
            tech_stack=["Python", "FastAPI", "PyTorch", "React"],
            description="CLI and dashboard for automated pull-request quality checks.",
            project_id="p2",
        ),
        Project.create(
            "Interactive Portfolio System",
            topic_id="t3",
            status="Completed",
            target_date="2026-10-01",
            hours_spent=45,
            repo_url="https://github.com/example/portfolio-v4",
            tech_stack=["React", "Tailwind CSS", "Vite", "Three.js"],
            description="Personal web canvas showcasing projects and study metrics.",
            project_id="p3",
        ),
    ]
    project_tasks = {
        "p1": [
            ("tk1", "Setup Kafka cluster with Docker Compose", True),
            ("tk2", "Implement Go worker pool consumer", True),
            ("tk3", "Add Elasticsearch indexing logic", False),
            ("tk4", "Benchmark performance under high load", False),
        ],
        "p2": [
            ("tk201", "Define API schema for PR webhook payload", True),
            ("tk202", "Test local LLM prompt engineering", False),
            ("tk203", "Build React UI diff viewer component", False),
        ],
        "p3": [
            ("tk301", "Design system setup in Tailwind", True),
            ("tk302", "Build dark mode state manager", True),
            ("tk303", "Deploy with automated CI/CD", True),
        ],
    }
    for project in projects:
        for task_id, title, completed in project_tasks[project.id]:
            task = project.add_task(title, task_id=task_id)
            task.completed = completed
        uow.projects.add(project)

    logs = [
        StudyLog.create(
            topic_id="t1",
            topic_title=architecture.title,
            hours="2.5",
            logged_on="2026-11-05",
            note="Learned consistent hashing for distributed caches.",
            log_id="l1",
        ),
        StudyLog.create(
            topic_id="t2",
            topic_title=machine_learning.title,
            hours="3.0",
            logged_on="2026-11-06",
            note="Worked through Transformer attention layer implementations.",
            log_id="l2",
        ),
        StudyLog.create(
            topic_id="t3",
            topic_title=design.title,
            hours="1.5",
            logged_on="2026-11-07",
            note="Refactored component tokens for dark mode support.",
            log_id="l3",
        ),
    ]
    for log in logs:
        uow.logs.add(log)
