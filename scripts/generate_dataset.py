"""Generate a deterministic, realistic books-catalog dataset.

Produces two files:
- data/books.csv  : suitable for Solr's /update/csv handler
- data/books.json : suitable for Solr's /update/json/docs handler

The dataset is hand-curated (titles, authors, genres) and deterministically
expanded to ~250 records by sampling and recombining the seed records. The
generator is reproducible: running it twice yields identical output.

Run:
    python scripts/generate_dataset.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEED_BOOKS: list[dict] = [
    {
        "title": "The Pragmatic Programmer",
        "author": "Andrew Hunt and David Thomas",
        "genres": ["Programming", "Software Engineering"],
        "language": "English",
        "year": 1999,
        "pages": 352,
        "rating": 4.6,
        "price": 39.99,
        "publisher": "Addison-Wesley",
        "tags": ["coding", "career", "best-practices"],
        "description": (
            "A modern classic that helps software developers move from journeyman "
            "to master through practical advice on craftsmanship, tooling, and "
            "the social aspects of building reliable software systems."
        ),
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "genres": ["Programming", "Software Engineering"],
        "language": "English",
        "year": 2008,
        "pages": 464,
        "rating": 4.4,
        "price": 35.50,
        "publisher": "Prentice Hall",
        "tags": ["coding", "refactoring", "design"],
        "description": (
            "A handbook of agile software craftsmanship that teaches developers "
            "how to write code that is easy to read, change, and maintain by "
            "applying simple, repeatable principles."
        ),
    },
    {
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "genres": ["Distributed Systems", "Databases"],
        "language": "English",
        "year": 2017,
        "pages": 616,
        "rating": 4.8,
        "price": 49.99,
        "publisher": "O'Reilly Media",
        "tags": ["databases", "scalability", "architecture"],
        "description": (
            "An indispensable guide to the architecture of modern data systems, "
            "covering replication, partitioning, transactions, consistency, and "
            "the trade-offs of stream and batch processing pipelines."
        ),
    },
    {
        "title": "Introduction to Algorithms",
        "author": "Thomas H. Cormen",
        "genres": ["Algorithms", "Computer Science"],
        "language": "English",
        "year": 2009,
        "pages": 1312,
        "rating": 4.5,
        "price": 89.00,
        "publisher": "MIT Press",
        "tags": ["algorithms", "data-structures", "academic"],
        "description": (
            "Comprehensive treatment of the modern study of computer algorithms, "
            "presenting a wide range of algorithms in depth with rigorous "
            "mathematical analysis suitable for advanced study."
        ),
    },
    {
        "title": "Structure and Interpretation of Computer Programs",
        "author": "Harold Abelson and Gerald Jay Sussman",
        "genres": ["Programming", "Computer Science"],
        "language": "English",
        "year": 1996,
        "pages": 657,
        "rating": 4.7,
        "price": 60.00,
        "publisher": "MIT Press",
        "tags": ["functional", "scheme", "classic"],
        "description": (
            "A foundational text that uses Scheme to introduce abstraction, "
            "modularity, and the principles of computation in a way that has "
            "shaped generations of programmers."
        ),
    },
    {
        "title": "The Mythical Man-Month",
        "author": "Frederick P. Brooks Jr.",
        "genres": ["Software Engineering", "Project Management"],
        "language": "English",
        "year": 1995,
        "pages": 322,
        "rating": 4.3,
        "price": 32.00,
        "publisher": "Addison-Wesley",
        "tags": ["project-management", "history", "essays"],
        "description": (
            "Brooks's seminal collection of essays on software engineering "
            "argues that adding manpower to a late project makes it later, and "
            "explores the human side of large-scale software development."
        ),
    },
    {
        "title": "Code Complete",
        "author": "Steve McConnell",
        "genres": ["Programming", "Software Engineering"],
        "language": "English",
        "year": 2004,
        "pages": 960,
        "rating": 4.4,
        "price": 45.00,
        "publisher": "Microsoft Press",
        "tags": ["construction", "best-practices"],
        "description": (
            "A practical handbook of software construction techniques that "
            "synthesizes research and experience into actionable advice for "
            "writing higher-quality code."
        ),
    },
    {
        "title": "Refactoring",
        "author": "Martin Fowler",
        "genres": ["Programming", "Software Engineering"],
        "language": "English",
        "year": 2018,
        "pages": 448,
        "rating": 4.5,
        "price": 47.99,
        "publisher": "Addison-Wesley",
        "tags": ["refactoring", "design", "patterns"],
        "description": (
            "A catalog of small, behavior-preserving transformations that "
            "improve the design of existing code, with worked examples and "
            "guidance on when each refactoring is appropriate."
        ),
    },
    {
        "title": "Designing Distributed Systems",
        "author": "Brendan Burns",
        "genres": ["Distributed Systems", "Cloud Computing"],
        "language": "English",
        "year": 2018,
        "pages": 166,
        "rating": 4.2,
        "price": 29.99,
        "publisher": "O'Reilly Media",
        "tags": ["kubernetes", "patterns", "microservices"],
        "description": (
            "Patterns and paradigms for designing reliable, scalable distributed "
            "systems built on container orchestration platforms such as "
            "Kubernetes."
        ),
    },
    {
        "title": "Site Reliability Engineering",
        "author": "Niall Richard Murphy and Betsy Beyer",
        "genres": ["DevOps", "Operations"],
        "language": "English",
        "year": 2016,
        "pages": 552,
        "rating": 4.3,
        "price": 44.99,
        "publisher": "O'Reilly Media",
        "tags": ["sre", "operations", "google"],
        "description": (
            "Google's principles and practices for running production systems, "
            "covering service-level objectives, error budgets, on-call culture, "
            "and post-mortem driven engineering."
        ),
    },
    {
        "title": "The Art of Computer Programming, Vol. 1",
        "author": "Donald E. Knuth",
        "genres": ["Algorithms", "Computer Science"],
        "language": "English",
        "year": 1997,
        "pages": 672,
        "rating": 4.7,
        "price": 99.00,
        "publisher": "Addison-Wesley",
        "tags": ["fundamentals", "math", "classic"],
        "description": (
            "Knuth's monumental treatise on the analysis of algorithms, beginning "
            "with the mathematical preliminaries needed for the deep study of "
            "computer programming."
        ),
    },
    {
        "title": "Database System Concepts",
        "author": "Abraham Silberschatz",
        "genres": ["Databases", "Computer Science"],
        "language": "English",
        "year": 2019,
        "pages": 1376,
        "rating": 4.2,
        "price": 95.00,
        "publisher": "McGraw-Hill",
        "tags": ["databases", "sql", "academic"],
        "description": (
            "A comprehensive introduction to database management systems "
            "covering relational theory, transaction processing, query "
            "optimization, and modern distributed data stores."
        ),
    },
    {
        "title": "Operating System Concepts",
        "author": "Abraham Silberschatz",
        "genres": ["Operating Systems", "Computer Science"],
        "language": "English",
        "year": 2018,
        "pages": 976,
        "rating": 4.1,
        "price": 88.00,
        "publisher": "Wiley",
        "tags": ["os", "academic", "kernel"],
        "description": (
            "The classic 'dinosaur book' on operating systems, presenting "
            "process management, memory, file systems, and synchronization "
            "with worked examples from real systems."
        ),
    },
    {
        "title": "Computer Networking: A Top-Down Approach",
        "author": "James F. Kurose and Keith W. Ross",
        "genres": ["Networking", "Computer Science"],
        "language": "English",
        "year": 2017,
        "pages": 864,
        "rating": 4.3,
        "price": 79.00,
        "publisher": "Pearson",
        "tags": ["networking", "tcp", "academic"],
        "description": (
            "A widely adopted networking textbook that introduces protocols and "
            "performance from the application layer down to the physical "
            "layer, with rich pedagogy and lab exercises."
        ),
    },
    {
        "title": "The Algorithm Design Manual",
        "author": "Steven S. Skiena",
        "genres": ["Algorithms", "Computer Science"],
        "language": "English",
        "year": 2020,
        "pages": 793,
        "rating": 4.5,
        "price": 64.99,
        "publisher": "Springer",
        "tags": ["algorithms", "interview", "practical"],
        "description": (
            "A practical guide to algorithm design with a hitchhiker-style "
            "catalog of common algorithmic problems and proven techniques for "
            "tackling them."
        ),
    },
    {
        "title": "Hands-On Machine Learning",
        "author": "Aurelien Geron",
        "genres": ["Machine Learning", "Data Science"],
        "language": "English",
        "year": 2019,
        "pages": 856,
        "rating": 4.7,
        "price": 59.99,
        "publisher": "O'Reilly Media",
        "tags": ["ml", "tensorflow", "scikit-learn"],
        "description": (
            "An applied tour of modern machine learning using Scikit-Learn, "
            "Keras, and TensorFlow, with end-to-end projects that illustrate "
            "best practices from data prep through deployment."
        ),
    },
    {
        "title": "Deep Learning",
        "author": "Ian Goodfellow",
        "genres": ["Machine Learning", "Artificial Intelligence"],
        "language": "English",
        "year": 2016,
        "pages": 800,
        "rating": 4.4,
        "price": 70.00,
        "publisher": "MIT Press",
        "tags": ["deep-learning", "neural-networks", "theory"],
        "description": (
            "An authoritative reference on deep learning that covers the "
            "mathematical and conceptual background, modern architectures, and "
            "research-frontier topics in representation learning."
        ),
    },
    {
        "title": "Python Crash Course",
        "author": "Eric Matthes",
        "genres": ["Programming", "Python"],
        "language": "English",
        "year": 2019,
        "pages": 544,
        "rating": 4.6,
        "price": 39.95,
        "publisher": "No Starch Press",
        "tags": ["python", "beginner", "projects"],
        "description": (
            "A fast-paced introduction to Python programming that takes "
            "complete beginners from the basics through three substantial "
            "projects in games, data, and web."
        ),
    },
    {
        "title": "Fluent Python",
        "author": "Luciano Ramalho",
        "genres": ["Programming", "Python"],
        "language": "English",
        "year": 2022,
        "pages": 1014,
        "rating": 4.7,
        "price": 65.99,
        "publisher": "O'Reilly Media",
        "tags": ["python", "advanced", "idioms"],
        "description": (
            "An expert tour of Python's most powerful features, showing how to "
            "write idiomatic, efficient code by leveraging the language's data "
            "model, descriptors, and concurrency primitives."
        ),
    },
    {
        "title": "Effective Java",
        "author": "Joshua Bloch",
        "genres": ["Programming", "Java"],
        "language": "English",
        "year": 2018,
        "pages": 412,
        "rating": 4.7,
        "price": 49.99,
        "publisher": "Addison-Wesley",
        "tags": ["java", "best-practices", "design"],
        "description": (
            "A collection of pragmatic, high-impact items on writing better "
            "Java, distilled from years of language-design experience and "
            "real-world API construction."
        ),
    },
    {
        "title": "Programming Pearls",
        "author": "Jon Bentley",
        "genres": ["Programming", "Algorithms"],
        "language": "English",
        "year": 1999,
        "pages": 256,
        "rating": 4.5,
        "price": 38.00,
        "publisher": "Addison-Wesley",
        "tags": ["essays", "problem-solving", "classic"],
        "description": (
            "A delightful set of essays on practical algorithm design and the "
            "craft of programming, distilled from columns originally written "
            "for Communications of the ACM."
        ),
    },
    {
        "title": "Cracking the Coding Interview",
        "author": "Gayle Laakmann McDowell",
        "genres": ["Algorithms", "Career"],
        "language": "English",
        "year": 2015,
        "pages": 696,
        "rating": 4.5,
        "price": 35.00,
        "publisher": "CareerCup",
        "tags": ["interview", "algorithms", "career"],
        "description": (
            "A comprehensive guide to technical interviews with 189 fully "
            "worked questions, covering algorithms, data structures, and the "
            "soft skills that hiring managers screen for."
        ),
    },
    {
        "title": "JavaScript: The Good Parts",
        "author": "Douglas Crockford",
        "genres": ["Programming", "JavaScript"],
        "language": "English",
        "year": 2008,
        "pages": 176,
        "rating": 4.1,
        "price": 28.99,
        "publisher": "O'Reilly Media",
        "tags": ["javascript", "language-design"],
        "description": (
            "A concise distillation of the elegant subset of JavaScript that "
            "lets developers avoid the language's well-known sharp edges and "
            "build robust software."
        ),
    },
    {
        "title": "You Don't Know JS Yet",
        "author": "Kyle Simpson",
        "genres": ["Programming", "JavaScript"],
        "language": "English",
        "year": 2020,
        "pages": 282,
        "rating": 4.4,
        "price": 32.50,
        "publisher": "Self-Published",
        "tags": ["javascript", "fundamentals", "series"],
        "description": (
            "A deep, no-shortcuts series that explores the core mechanics of "
            "JavaScript from scoping and closures to types, coercion, and the "
            "asynchronous model."
        ),
    },
    {
        "title": "Eloquent JavaScript",
        "author": "Marijn Haverbeke",
        "genres": ["Programming", "JavaScript"],
        "language": "English",
        "year": 2018,
        "pages": 472,
        "rating": 4.5,
        "price": 39.95,
        "publisher": "No Starch Press",
        "tags": ["javascript", "beginner", "projects"],
        "description": (
            "A modern introduction to programming with JavaScript that "
            "combines language fundamentals with browser, Node.js, and "
            "interactive project chapters."
        ),
    },
    {
        "title": "The C Programming Language",
        "author": "Brian W. Kernighan and Dennis M. Ritchie",
        "genres": ["Programming", "C"],
        "language": "English",
        "year": 1988,
        "pages": 272,
        "rating": 4.7,
        "price": 42.00,
        "publisher": "Prentice Hall",
        "tags": ["c", "classic", "fundamentals"],
        "description": (
            "The definitive reference to ANSI C, written by the creators of "
            "the language with the disciplined clarity that made it a "
            "permanent fixture of every programmer's bookshelf."
        ),
    },
    {
        "title": "Compilers: Principles, Techniques, and Tools",
        "author": "Alfred V. Aho",
        "genres": ["Compilers", "Computer Science"],
        "language": "English",
        "year": 2006,
        "pages": 1009,
        "rating": 4.3,
        "price": 95.00,
        "publisher": "Pearson",
        "tags": ["compilers", "academic", "dragon"],
        "description": (
            "The 'Dragon Book' covering lexical analysis, parsing, semantic "
            "analysis, intermediate code generation, optimization, and code "
            "generation for modern compilers."
        ),
    },
    {
        "title": "Computer Systems: A Programmer's Perspective",
        "author": "Randal E. Bryant and David R. O'Hallaron",
        "genres": ["Computer Architecture", "Operating Systems"],
        "language": "English",
        "year": 2015,
        "pages": 1072,
        "rating": 4.6,
        "price": 90.00,
        "publisher": "Pearson",
        "tags": ["systems", "x86", "linking"],
        "description": (
            "Examines computer systems from the programmer's viewpoint, "
            "covering data representation, processor architecture, the memory "
            "hierarchy, linking, exceptions, and concurrency."
        ),
    },
    {
        "title": "Domain-Driven Design",
        "author": "Eric Evans",
        "genres": ["Software Engineering", "Architecture"],
        "language": "English",
        "year": 2003,
        "pages": 560,
        "rating": 4.3,
        "price": 49.99,
        "publisher": "Addison-Wesley",
        "tags": ["ddd", "modeling", "architecture"],
        "description": (
            "Tackling software complexity in the heart of business logic, "
            "Evans introduces a vocabulary and a set of practices for "
            "modeling rich domains in collaboration with experts."
        ),
    },
    {
        "title": "Patterns of Enterprise Application Architecture",
        "author": "Martin Fowler",
        "genres": ["Software Engineering", "Architecture"],
        "language": "English",
        "year": 2002,
        "pages": 560,
        "rating": 4.3,
        "price": 54.99,
        "publisher": "Addison-Wesley",
        "tags": ["patterns", "enterprise", "architecture"],
        "description": (
            "A catalog of architectural patterns for building enterprise "
            "applications, covering data mapping, concurrency, session "
            "state, and distribution strategies."
        ),
    },
    {
        "title": "Working Effectively with Legacy Code",
        "author": "Michael C. Feathers",
        "genres": ["Software Engineering", "Refactoring"],
        "language": "English",
        "year": 2004,
        "pages": 456,
        "rating": 4.4,
        "price": 41.99,
        "publisher": "Prentice Hall",
        "tags": ["legacy", "testing", "refactoring"],
        "description": (
            "Practical techniques for stabilizing, testing, and extending "
            "untested codebases by introducing seams and isolating "
            "dependencies in safe, incremental steps."
        ),
    },
    {
        "title": "Cloud Native Patterns",
        "author": "Cornelia Davis",
        "genres": ["Cloud Computing", "Architecture"],
        "language": "English",
        "year": 2019,
        "pages": 400,
        "rating": 4.0,
        "price": 49.99,
        "publisher": "Manning",
        "tags": ["cloud", "patterns", "12-factor"],
        "description": (
            "Concepts and patterns for designing applications that take full "
            "advantage of dynamic, distributed cloud environments — service "
            "discovery, resilience, and observability."
        ),
    },
    {
        "title": "The DevOps Handbook",
        "author": "Gene Kim",
        "genres": ["DevOps", "Software Engineering"],
        "language": "English",
        "year": 2016,
        "pages": 480,
        "rating": 4.5,
        "price": 39.99,
        "publisher": "IT Revolution Press",
        "tags": ["devops", "culture", "automation"],
        "description": (
            "A guide to applying the principles described in The Phoenix "
            "Project to real organizations, with case studies that "
            "demonstrate how to align development and operations."
        ),
    },
    {
        "title": "Accelerate",
        "author": "Nicole Forsgren",
        "genres": ["DevOps", "Research"],
        "language": "English",
        "year": 2018,
        "pages": 252,
        "rating": 4.5,
        "price": 27.95,
        "publisher": "IT Revolution Press",
        "tags": ["devops", "metrics", "research"],
        "description": (
            "An evidence-based exploration of the practices that drive high "
            "software-delivery performance, summarizing four years of State "
            "of DevOps research."
        ),
    },
    {
        "title": "The Phoenix Project",
        "author": "Gene Kim",
        "genres": ["DevOps", "Fiction"],
        "language": "English",
        "year": 2013,
        "pages": 432,
        "rating": 4.6,
        "price": 26.99,
        "publisher": "IT Revolution Press",
        "tags": ["devops", "novel", "lean"],
        "description": (
            "A business novel that follows an IT manager whose company is on "
            "the verge of collapse and the lessons he learns about applying "
            "lean principles to software delivery."
        ),
    },
    {
        "title": "Kubernetes Up & Running",
        "author": "Brendan Burns",
        "genres": ["Cloud Computing", "DevOps"],
        "language": "English",
        "year": 2019,
        "pages": 278,
        "rating": 4.3,
        "price": 39.99,
        "publisher": "O'Reilly Media",
        "tags": ["kubernetes", "containers", "ops"],
        "description": (
            "A practical guide to deploying and operating containerized "
            "applications on Kubernetes, with hands-on examples covering "
            "scaling, security, and storage."
        ),
    },
    {
        "title": "Docker Deep Dive",
        "author": "Nigel Poulton",
        "genres": ["Cloud Computing", "DevOps"],
        "language": "English",
        "year": 2020,
        "pages": 426,
        "rating": 4.6,
        "price": 35.00,
        "publisher": "Self-Published",
        "tags": ["docker", "containers", "ops"],
        "description": (
            "A thorough yet readable tour of Docker covering images, "
            "containers, networking, storage, swarm mode, and the broader "
            "container ecosystem."
        ),
    },
    {
        "title": "Lucene in Action",
        "author": "Michael McCandless",
        "genres": ["Information Retrieval", "Search"],
        "language": "English",
        "year": 2010,
        "pages": 528,
        "rating": 4.2,
        "price": 49.99,
        "publisher": "Manning",
        "tags": ["lucene", "search", "indexing"],
        "description": (
            "An in-depth exploration of Apache Lucene, covering indexing, "
            "searching, analyzers, and the techniques used to build powerful "
            "full-text search applications."
        ),
    },
    {
        "title": "Solr in Action",
        "author": "Trey Grainger",
        "genres": ["Information Retrieval", "Search"],
        "language": "English",
        "year": 2014,
        "pages": 664,
        "rating": 4.3,
        "price": 49.99,
        "publisher": "Manning",
        "tags": ["solr", "lucene", "search"],
        "description": (
            "A comprehensive guide to Apache Solr that covers schema design, "
            "scoring, faceting, distributed search, and the operational "
            "aspects of running Solr in production."
        ),
    },
    {
        "title": "Elasticsearch: The Definitive Guide",
        "author": "Clinton Gormley",
        "genres": ["Information Retrieval", "Search"],
        "language": "English",
        "year": 2015,
        "pages": 720,
        "rating": 4.4,
        "price": 49.99,
        "publisher": "O'Reilly Media",
        "tags": ["elasticsearch", "lucene", "search"],
        "description": (
            "An authoritative introduction to Elasticsearch covering "
            "indexing, querying, analysis, aggregations, and the operational "
            "concerns of running a clustered search service."
        ),
    },
    {
        "title": "Hadoop: The Definitive Guide",
        "author": "Tom White",
        "genres": ["Big Data", "Distributed Systems"],
        "language": "English",
        "year": 2015,
        "pages": 756,
        "rating": 4.3,
        "price": 49.99,
        "publisher": "O'Reilly Media",
        "tags": ["hadoop", "mapreduce", "hdfs"],
        "description": (
            "The standard reference for Apache Hadoop, covering HDFS, "
            "MapReduce, YARN, and the surrounding ecosystem with practical "
            "guidance on operating production clusters."
        ),
    },
    {
        "title": "Spark: The Definitive Guide",
        "author": "Bill Chambers and Matei Zaharia",
        "genres": ["Big Data", "Distributed Systems"],
        "language": "English",
        "year": 2018,
        "pages": 624,
        "rating": 4.4,
        "price": 49.99,
        "publisher": "O'Reilly Media",
        "tags": ["spark", "scala", "data-processing"],
        "description": (
            "A comprehensive guide to Apache Spark covering the structured "
            "APIs, streaming, machine learning, and tuning techniques for "
            "large-scale data processing."
        ),
    },
    {
        "title": "Streaming Systems",
        "author": "Tyler Akidau",
        "genres": ["Big Data", "Distributed Systems"],
        "language": "English",
        "year": 2018,
        "pages": 380,
        "rating": 4.6,
        "price": 49.99,
        "publisher": "O'Reilly Media",
        "tags": ["streaming", "kafka", "beam"],
        "description": (
            "A modern treatment of unbounded data processing that introduces "
            "the principles behind streaming systems, the Beam model, and "
            "exactly-once delivery semantics."
        ),
    },
    {
        "title": "Building Microservices",
        "author": "Sam Newman",
        "genres": ["Software Engineering", "Architecture"],
        "language": "English",
        "year": 2021,
        "pages": 612,
        "rating": 4.4,
        "price": 49.99,
        "publisher": "O'Reilly Media",
        "tags": ["microservices", "architecture", "patterns"],
        "description": (
            "A practical guide to designing fine-grained services with clear "
            "boundaries, independent deployability, and resilience strategies "
            "for the operational realities of distributed systems."
        ),
    },
    {
        "title": "Software Engineering at Google",
        "author": "Titus Winters",
        "genres": ["Software Engineering", "Engineering Culture"],
        "language": "English",
        "year": 2020,
        "pages": 602,
        "rating": 4.4,
        "price": 49.99,
        "publisher": "O'Reilly Media",
        "tags": ["culture", "process", "scale"],
        "description": (
            "Lessons learned from programming over time at Google scale, with "
            "a focus on culture, processes, and tools that allow teams to "
            "build software that lasts."
        ),
    },
    {
        "title": "Don't Make Me Think",
        "author": "Steve Krug",
        "genres": ["UX Design", "Web"],
        "language": "English",
        "year": 2014,
        "pages": 200,
        "rating": 4.6,
        "price": 28.00,
        "publisher": "New Riders",
        "tags": ["usability", "ux", "web"],
        "description": (
            "A common-sense approach to web usability that has guided "
            "designers and developers for two decades to build interfaces "
            "people actually understand."
        ),
    },
    {
        "title": "The Design of Everyday Things",
        "author": "Don Norman",
        "genres": ["UX Design", "Psychology"],
        "language": "English",
        "year": 2013,
        "pages": 368,
        "rating": 4.5,
        "price": 18.99,
        "publisher": "Basic Books",
        "tags": ["design", "cognition", "affordance"],
        "description": (
            "A foundational text in user-centered design that examines how "
            "everyday objects succeed or fail at communicating their "
            "purpose to the humans who use them."
        ),
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "genres": ["Fiction", "Dystopian"],
        "language": "English",
        "year": 1949,
        "pages": 328,
        "rating": 4.4,
        "price": 14.99,
        "publisher": "Secker & Warburg",
        "tags": ["classic", "totalitarianism", "surveillance"],
        "description": (
            "Orwell's chilling portrait of a totalitarian future in which "
            "the state controls thought through language, surveillance, and "
            "perpetual war."
        ),
    },
    {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "genres": ["Fiction", "Classic"],
        "language": "English",
        "year": 1960,
        "pages": 281,
        "rating": 4.6,
        "price": 12.99,
        "publisher": "J. B. Lippincott",
        "tags": ["classic", "justice", "south"],
        "description": (
            "A coming-of-age story set in Depression-era Alabama in which a "
            "young girl's father defends a Black man falsely accused of a "
            "terrible crime."
        ),
    },
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "genres": ["Fiction", "Classic"],
        "language": "English",
        "year": 1925,
        "pages": 180,
        "rating": 4.0,
        "price": 11.99,
        "publisher": "Scribner",
        "tags": ["classic", "jazz-age", "tragedy"],
        "description": (
            "A lyrical chronicle of obsession and the American Dream set in "
            "the roaring twenties of Long Island and Manhattan."
        ),
    },
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "genres": ["Fiction", "Romance"],
        "language": "English",
        "year": 1813,
        "pages": 432,
        "rating": 4.4,
        "price": 10.99,
        "publisher": "T. Egerton",
        "tags": ["classic", "regency", "romance"],
        "description": (
            "Austen's witty study of manners, marriage, and the gradual "
            "softening of first impressions in early-19th-century English "
            "society."
        ),
    },
    {
        "title": "One Hundred Years of Solitude",
        "author": "Gabriel Garcia Marquez",
        "genres": ["Fiction", "Magical Realism"],
        "language": "Spanish",
        "year": 1967,
        "pages": 417,
        "rating": 4.4,
        "price": 16.99,
        "publisher": "Editorial Sudamericana",
        "tags": ["magical-realism", "latin-america", "epic"],
        "description": (
            "The multi-generational saga of the Buendia family in the "
            "fictional town of Macondo, a foundational work of magical "
            "realism."
        ),
    },
    {
        "title": "The Brothers Karamazov",
        "author": "Fyodor Dostoevsky",
        "genres": ["Fiction", "Philosophy"],
        "language": "Russian",
        "year": 1880,
        "pages": 796,
        "rating": 4.5,
        "price": 18.99,
        "publisher": "The Russian Messenger",
        "tags": ["classic", "philosophy", "russian"],
        "description": (
            "A philosophical novel that explores faith, doubt, and free will "
            "through the conflicts of three brothers and the murder of their "
            "dissolute father."
        ),
    },
    {
        "title": "Crime and Punishment",
        "author": "Fyodor Dostoevsky",
        "genres": ["Fiction", "Psychological"],
        "language": "Russian",
        "year": 1866,
        "pages": 671,
        "rating": 4.4,
        "price": 14.99,
        "publisher": "The Russian Messenger",
        "tags": ["classic", "psychology", "russian"],
        "description": (
            "A poor former student in St. Petersburg commits a murder and is "
            "haunted by the moral and psychological consequences of his act."
        ),
    },
    {
        "title": "War and Peace",
        "author": "Leo Tolstoy",
        "genres": ["Fiction", "Historical"],
        "language": "Russian",
        "year": 1869,
        "pages": 1225,
        "rating": 4.3,
        "price": 22.99,
        "publisher": "The Russian Messenger",
        "tags": ["epic", "history", "napoleonic"],
        "description": (
            "Tolstoy's panoramic Napoleonic-era novel that interweaves the "
            "fates of five aristocratic families with sweeping reflections on "
            "history."
        ),
    },
    {
        "title": "Anna Karenina",
        "author": "Leo Tolstoy",
        "genres": ["Fiction", "Romance"],
        "language": "Russian",
        "year": 1878,
        "pages": 864,
        "rating": 4.3,
        "price": 16.99,
        "publisher": "The Russian Messenger",
        "tags": ["classic", "russian", "tragedy"],
        "description": (
            "A devastating exploration of love, faith, and society told "
            "through the parallel stories of Anna Karenina's tragic affair "
            "and Levin's search for meaning."
        ),
    },
    {
        "title": "The Hobbit",
        "author": "J. R. R. Tolkien",
        "genres": ["Fiction", "Fantasy"],
        "language": "English",
        "year": 1937,
        "pages": 310,
        "rating": 4.7,
        "price": 14.99,
        "publisher": "George Allen & Unwin",
        "tags": ["fantasy", "adventure", "middle-earth"],
        "description": (
            "Bilbo Baggins is whisked from his comfortable hobbit-hole on a "
            "quest to help a company of dwarves reclaim their mountain home "
            "from the dragon Smaug."
        ),
    },
    {
        "title": "The Lord of the Rings",
        "author": "J. R. R. Tolkien",
        "genres": ["Fiction", "Fantasy"],
        "language": "English",
        "year": 1954,
        "pages": 1178,
        "rating": 4.8,
        "price": 29.99,
        "publisher": "George Allen & Unwin",
        "tags": ["fantasy", "epic", "middle-earth"],
        "description": (
            "The epic tale of the Fellowship's quest to destroy the One Ring "
            "and overthrow the dark lord Sauron, a foundational text of "
            "modern fantasy."
        ),
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "genres": ["Fiction", "Science Fiction"],
        "language": "English",
        "year": 1965,
        "pages": 688,
        "rating": 4.6,
        "price": 19.99,
        "publisher": "Chilton Books",
        "tags": ["sci-fi", "epic", "politics"],
        "description": (
            "On the desert planet Arrakis, the only source of the universe's "
            "most valuable substance, a young noble must navigate ecology, "
            "religion, and intergalactic politics."
        ),
    },
    {
        "title": "Foundation",
        "author": "Isaac Asimov",
        "genres": ["Fiction", "Science Fiction"],
        "language": "English",
        "year": 1951,
        "pages": 244,
        "rating": 4.3,
        "price": 13.99,
        "publisher": "Gnome Press",
        "tags": ["sci-fi", "classic", "psychohistory"],
        "description": (
            "Mathematician Hari Seldon predicts the fall of a galactic "
            "empire and creates a foundation that aims to shorten the "
            "approaching age of barbarism."
        ),
    },
    {
        "title": "Neuromancer",
        "author": "William Gibson",
        "genres": ["Fiction", "Science Fiction"],
        "language": "English",
        "year": 1984,
        "pages": 271,
        "rating": 4.0,
        "price": 14.99,
        "publisher": "Ace Books",
        "tags": ["cyberpunk", "ai", "classic"],
        "description": (
            "A washed-up hacker is given a chance at redemption in a noir-"
            "tinged future where AI, mega-corporations, and human "
            "consciousness collide."
        ),
    },
    {
        "title": "Snow Crash",
        "author": "Neal Stephenson",
        "genres": ["Fiction", "Science Fiction"],
        "language": "English",
        "year": 1992,
        "pages": 480,
        "rating": 4.0,
        "price": 16.99,
        "publisher": "Bantam",
        "tags": ["cyberpunk", "metaverse", "satire"],
        "description": (
            "A pizza-delivering hacker uncovers a virtual virus that "
            "threatens both the digital Metaverse and the physical world in "
            "this prescient cyberpunk satire."
        ),
    },
    {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "genres": ["Fiction", "Dystopian"],
        "language": "English",
        "year": 1932,
        "pages": 311,
        "rating": 4.0,
        "price": 13.99,
        "publisher": "Chatto & Windus",
        "tags": ["classic", "dystopia", "satire"],
        "description": (
            "A future society engineered for maximum stability and pleasure "
            "is disturbed by the arrival of an outsider who has known a "
            "different way of life."
        ),
    },
    {
        "title": "Fahrenheit 451",
        "author": "Ray Bradbury",
        "genres": ["Fiction", "Dystopian"],
        "language": "English",
        "year": 1953,
        "pages": 249,
        "rating": 4.0,
        "price": 12.99,
        "publisher": "Ballantine Books",
        "tags": ["classic", "dystopia", "books"],
        "description": (
            "In a future where books are outlawed and burned by 'firemen', "
            "one fireman begins to question the world he enforces and the "
            "stories he is destroying."
        ),
    },
    {
        "title": "The Catcher in the Rye",
        "author": "J. D. Salinger",
        "genres": ["Fiction", "Classic"],
        "language": "English",
        "year": 1951,
        "pages": 277,
        "rating": 3.8,
        "price": 12.99,
        "publisher": "Little, Brown",
        "tags": ["classic", "coming-of-age"],
        "description": (
            "Holden Caulfield's three-day odyssey through New York City "
            "captures the alienation, anger, and tenderness of adolescence "
            "with extraordinary voice."
        ),
    },
    {
        "title": "Beloved",
        "author": "Toni Morrison",
        "genres": ["Fiction", "Historical"],
        "language": "English",
        "year": 1987,
        "pages": 324,
        "rating": 4.0,
        "price": 15.99,
        "publisher": "Knopf",
        "tags": ["pulitzer", "history", "memory"],
        "description": (
            "A formerly enslaved woman's house is haunted by the ghost of her "
            "dead daughter in this Pulitzer-winning meditation on memory and "
            "freedom."
        ),
    },
    {
        "title": "The Road",
        "author": "Cormac McCarthy",
        "genres": ["Fiction", "Post-Apocalyptic"],
        "language": "English",
        "year": 2006,
        "pages": 287,
        "rating": 4.0,
        "price": 16.00,
        "publisher": "Knopf",
        "tags": ["post-apocalyptic", "father-son"],
        "description": (
            "A father and son traverse a scorched, post-apocalyptic America "
            "in McCarthy's spare and devastating exploration of love and "
            "survival."
        ),
    },
    {
        "title": "Sapiens",
        "author": "Yuval Noah Harari",
        "genres": ["Non-Fiction", "History"],
        "language": "English",
        "year": 2014,
        "pages": 443,
        "rating": 4.4,
        "price": 24.99,
        "publisher": "Harper",
        "tags": ["history", "anthropology"],
        "description": (
            "A sweeping account of how Homo sapiens came to dominate the "
            "planet, weaving together biology, history, and economics into a "
            "single narrative."
        ),
    },
    {
        "title": "Thinking, Fast and Slow",
        "author": "Daniel Kahneman",
        "genres": ["Non-Fiction", "Psychology"],
        "language": "English",
        "year": 2011,
        "pages": 499,
        "rating": 4.2,
        "price": 18.99,
        "publisher": "Farrar, Straus and Giroux",
        "tags": ["cognition", "decision-making"],
        "description": (
            "Nobel laureate Daniel Kahneman explores the two systems that "
            "drive the way we think, exposing the biases and shortcuts that "
            "shape every decision we make."
        ),
    },
    {
        "title": "Atomic Habits",
        "author": "James Clear",
        "genres": ["Non-Fiction", "Self-Help"],
        "language": "English",
        "year": 2018,
        "pages": 320,
        "rating": 4.7,
        "price": 27.00,
        "publisher": "Avery",
        "tags": ["habits", "productivity"],
        "description": (
            "A practical framework for building good habits and breaking bad "
            "ones by focusing on tiny, compounding changes to identity and "
            "environment."
        ),
    },
    {
        "title": "The Lean Startup",
        "author": "Eric Ries",
        "genres": ["Non-Fiction", "Business"],
        "language": "English",
        "year": 2011,
        "pages": 336,
        "rating": 4.1,
        "price": 26.00,
        "publisher": "Crown Business",
        "tags": ["startup", "lean", "product"],
        "description": (
            "A methodology for launching products and businesses based on "
            "validated learning, rapid experimentation, and iterative "
            "release cycles."
        ),
    },
    {
        "title": "Zero to One",
        "author": "Peter Thiel",
        "genres": ["Non-Fiction", "Business"],
        "language": "English",
        "year": 2014,
        "pages": 224,
        "rating": 4.2,
        "price": 27.00,
        "publisher": "Crown Business",
        "tags": ["startup", "monopoly", "innovation"],
        "description": (
            "Notes on startups, or how to build the future, distilled from "
            "Thiel's Stanford lectures on the contrarian thinking required "
            "to create breakthrough companies."
        ),
    },
    {
        "title": "Good to Great",
        "author": "Jim Collins",
        "genres": ["Non-Fiction", "Business"],
        "language": "English",
        "year": 2001,
        "pages": 320,
        "rating": 4.1,
        "price": 30.00,
        "publisher": "HarperBusiness",
        "tags": ["leadership", "management"],
        "description": (
            "A research-driven look at what distinguishes companies that "
            "achieve sustained excellence from their merely good peers, with "
            "concrete principles for leaders."
        ),
    },
    {
        "title": "The Wealth of Nations",
        "author": "Adam Smith",
        "genres": ["Non-Fiction", "Economics"],
        "language": "English",
        "year": 1776,
        "pages": 1264,
        "rating": 3.9,
        "price": 24.00,
        "publisher": "W. Strahan",
        "tags": ["classic", "economics", "philosophy"],
        "description": (
            "Adam Smith's foundational treatise on economics, exploring the "
            "division of labour, free markets, and the accumulation of "
            "wealth in modern society."
        ),
    },
    {
        "title": "Capital in the Twenty-First Century",
        "author": "Thomas Piketty",
        "genres": ["Non-Fiction", "Economics"],
        "language": "French",
        "year": 2013,
        "pages": 696,
        "rating": 4.1,
        "price": 39.95,
        "publisher": "Belknap Press",
        "tags": ["economics", "inequality"],
        "description": (
            "A data-rich analysis of wealth and income inequality in Europe "
            "and the United States since the 18th century and the forces "
            "that shape its trajectory."
        ),
    },
    {
        "title": "A Brief History of Time",
        "author": "Stephen Hawking",
        "genres": ["Non-Fiction", "Physics"],
        "language": "English",
        "year": 1988,
        "pages": 256,
        "rating": 4.2,
        "price": 18.00,
        "publisher": "Bantam",
        "tags": ["cosmology", "popular-science"],
        "description": (
            "Hawking's landmark popular-science account of cosmology, from "
            "the Big Bang to black holes, written for readers without a "
            "scientific background."
        ),
    },
    {
        "title": "The Selfish Gene",
        "author": "Richard Dawkins",
        "genres": ["Non-Fiction", "Biology"],
        "language": "English",
        "year": 1976,
        "pages": 360,
        "rating": 4.1,
        "price": 17.95,
        "publisher": "Oxford University Press",
        "tags": ["evolution", "biology"],
        "description": (
            "Dawkins's gene-centred view of evolution, introducing the "
            "concept of the meme and reframing natural selection in terms "
            "of replicators."
        ),
    },
    {
        "title": "Cosmos",
        "author": "Carl Sagan",
        "genres": ["Non-Fiction", "Astronomy"],
        "language": "English",
        "year": 1980,
        "pages": 396,
        "rating": 4.4,
        "price": 18.99,
        "publisher": "Random House",
        "tags": ["space", "popular-science"],
        "description": (
            "Sagan's poetic and panoramic tour of the universe, weaving "
            "together cosmology, history, and the human quest to understand "
            "our place in the cosmos."
        ),
    },
    {
        "title": "The Origin of Species",
        "author": "Charles Darwin",
        "genres": ["Non-Fiction", "Biology"],
        "language": "English",
        "year": 1859,
        "pages": 502,
        "rating": 4.2,
        "price": 14.99,
        "publisher": "John Murray",
        "tags": ["evolution", "classic", "science"],
        "description": (
            "Darwin's revolutionary work introducing the theory of evolution "
            "by natural selection through extensive observations and "
            "synthesis of natural history."
        ),
    },
    {
        "title": "Silent Spring",
        "author": "Rachel Carson",
        "genres": ["Non-Fiction", "Environment"],
        "language": "English",
        "year": 1962,
        "pages": 368,
        "rating": 4.2,
        "price": 16.99,
        "publisher": "Houghton Mifflin",
        "tags": ["environment", "pesticides", "classic"],
        "description": (
            "Carson's wake-up call about the environmental cost of "
            "pesticides that helped launch the modern environmental "
            "movement."
        ),
    },
    {
        "title": "Steve Jobs",
        "author": "Walter Isaacson",
        "genres": ["Biography", "Business"],
        "language": "English",
        "year": 2011,
        "pages": 656,
        "rating": 4.4,
        "price": 22.00,
        "publisher": "Simon & Schuster",
        "tags": ["biography", "tech", "apple"],
        "description": (
            "An authorized biography of Apple's co-founder based on hundreds "
            "of interviews, painting a complex portrait of one of the "
            "tech industry's most influential leaders."
        ),
    },
    {
        "title": "Elon Musk",
        "author": "Walter Isaacson",
        "genres": ["Biography", "Business"],
        "language": "English",
        "year": 2023,
        "pages": 688,
        "rating": 4.0,
        "price": 35.00,
        "publisher": "Simon & Schuster",
        "tags": ["biography", "tech", "spacex"],
        "description": (
            "Isaacson's deeply reported biography of Elon Musk, exploring "
            "the personal and professional forces that drive the founder of "
            "Tesla and SpaceX."
        ),
    },
    {
        "title": "Born a Crime",
        "author": "Trevor Noah",
        "genres": ["Biography", "Memoir"],
        "language": "English",
        "year": 2016,
        "pages": 304,
        "rating": 4.7,
        "price": 17.00,
        "publisher": "Spiegel & Grau",
        "tags": ["memoir", "south-africa"],
        "description": (
            "Comedian Trevor Noah's memoir of growing up under apartheid in "
            "South Africa, told with humor and unsparing honesty about "
            "race, family, and resilience."
        ),
    },
    {
        "title": "Educated",
        "author": "Tara Westover",
        "genres": ["Biography", "Memoir"],
        "language": "English",
        "year": 2018,
        "pages": 334,
        "rating": 4.5,
        "price": 18.99,
        "publisher": "Random House",
        "tags": ["memoir", "education", "family"],
        "description": (
            "A memoir of self-invention by a woman raised by survivalist "
            "parents in Idaho who eventually earned a PhD from the "
            "University of Cambridge."
        ),
    },
    {
        "title": "When Breath Becomes Air",
        "author": "Paul Kalanithi",
        "genres": ["Biography", "Memoir"],
        "language": "English",
        "year": 2016,
        "pages": 228,
        "rating": 4.6,
        "price": 16.99,
        "publisher": "Random House",
        "tags": ["memoir", "medicine", "mortality"],
        "description": (
            "A neurosurgeon's poignant meditation on identity, meaning, and "
            "mortality after a terminal cancer diagnosis cuts short a "
            "promising career."
        ),
    },
    {
        "title": "The Diary of a Young Girl",
        "author": "Anne Frank",
        "genres": ["Biography", "History"],
        "language": "Dutch",
        "year": 1947,
        "pages": 283,
        "rating": 4.5,
        "price": 12.00,
        "publisher": "Contact Publishing",
        "tags": ["wwii", "memoir", "classic"],
        "description": (
            "The diary of a Jewish teenager hiding from the Nazis in "
            "occupied Amsterdam, an enduring testament to humanity in the "
            "face of horror."
        ),
    },
    {
        "title": "Long Walk to Freedom",
        "author": "Nelson Mandela",
        "genres": ["Biography", "History"],
        "language": "English",
        "year": 1994,
        "pages": 656,
        "rating": 4.6,
        "price": 22.00,
        "publisher": "Little, Brown",
        "tags": ["memoir", "south-africa", "politics"],
        "description": (
            "Nelson Mandela's autobiography, recounting his childhood, the "
            "long struggle against apartheid, and the road from prison cell "
            "to presidency."
        ),
    },
    {
        "title": "The Power of Habit",
        "author": "Charles Duhigg",
        "genres": ["Non-Fiction", "Psychology"],
        "language": "English",
        "year": 2012,
        "pages": 371,
        "rating": 4.1,
        "price": 18.00,
        "publisher": "Random House",
        "tags": ["habits", "productivity", "psychology"],
        "description": (
            "Why we do what we do in life and business, told through "
            "stories from Olympic athletes, Pepsodent executives, and "
            "civil-rights movements."
        ),
    },
    {
        "title": "Outliers",
        "author": "Malcolm Gladwell",
        "genres": ["Non-Fiction", "Psychology"],
        "language": "English",
        "year": 2008,
        "pages": 309,
        "rating": 4.2,
        "price": 18.00,
        "publisher": "Little, Brown",
        "tags": ["sociology", "success"],
        "description": (
            "Gladwell's exploration of the cultural, social, and statistical "
            "forces that produce extraordinarily successful people — "
            "popularizing the 10,000-hours rule."
        ),
    },
    {
        "title": "Blink",
        "author": "Malcolm Gladwell",
        "genres": ["Non-Fiction", "Psychology"],
        "language": "English",
        "year": 2005,
        "pages": 296,
        "rating": 4.0,
        "price": 17.00,
        "publisher": "Little, Brown",
        "tags": ["psychology", "decision-making"],
        "description": (
            "An investigation into the power of split-second decisions and "
            "how rapid cognition can be more reliable than careful "
            "deliberation — except when it isn't."
        ),
    },
    {
        "title": "The Tipping Point",
        "author": "Malcolm Gladwell",
        "genres": ["Non-Fiction", "Sociology"],
        "language": "English",
        "year": 2000,
        "pages": 301,
        "rating": 4.0,
        "price": 17.00,
        "publisher": "Little, Brown",
        "tags": ["sociology", "trends"],
        "description": (
            "How little things can make a big difference — Gladwell's "
            "examination of the moments when ideas, behaviors, and "
            "products cross a threshold and spread like wildfire."
        ),
    },
]

LANGUAGES = ["English", "French", "German", "Spanish", "Russian", "Chinese", "Japanese", "Arabic"]
PUBLISHERS = [
    "O'Reilly Media", "Manning", "Addison-Wesley", "MIT Press", "Penguin Classics",
    "Random House", "HarperCollins", "Vintage", "Knopf", "Simon & Schuster",
]


def make_isbn(seed: str) -> str:
    digest = hashlib.sha1(seed.encode()).hexdigest()
    digits = "".join(ch for ch in digest if ch.isdigit())
    base = "978" + (digits + "0" * 13)[:9]
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base))
    check = (10 - total % 10) % 10
    return base + str(check)


def expand(records: list[dict]) -> list[dict]:
    rng = random.Random(20260509)
    out: list[dict] = []
    next_id = 1
    for rec in records:
        rec = dict(rec)
        rec["id"] = f"book_{next_id:04d}"
        rec["isbn"] = make_isbn(rec["title"] + rec["author"])
        rec["in_stock"] = rng.random() < 0.85
        rec["stock_count"] = rng.randint(0, 250)
        rec["pub_date"] = f"{rec['year']:04d}-01-01T00:00:00Z"
        out.append(rec)
        next_id += 1

    edition_words = ["Companion", "Workbook", "Solutions Manual", "Annotated Edition", "Field Guide"]
    while len(out) < 250:
        base = rng.choice(records)
        edition = rng.choice(edition_words)
        title = f"{base['title']}: {edition}"
        author = base["author"]
        year = max(1700, base["year"] + rng.randint(-3, 8))
        rec = {
            "id": f"book_{next_id:04d}",
            "title": title,
            "author": author,
            "genres": base["genres"],
            "language": rng.choice(LANGUAGES) if rng.random() < 0.15 else base["language"],
            "year": year,
            "pages": max(80, base["pages"] + rng.randint(-120, 200)),
            "rating": round(min(5.0, max(2.5, base["rating"] + rng.uniform(-0.6, 0.4))), 1),
            "price": round(max(5.0, base["price"] + rng.uniform(-10, 20)), 2),
            "publisher": rng.choice(PUBLISHERS) if rng.random() < 0.2 else base["publisher"],
            "tags": sorted(set(base["tags"] + [edition.split()[0].lower()])),
            "description": (
                f"A companion volume to {base['title']} that revisits the "
                f"original's themes from a fresh angle, with updated "
                f"examples and exercises drawn from the {edition.lower()} "
                f"tradition."
            ),
            "isbn": make_isbn(title + author),
            "in_stock": rng.random() < 0.7,
            "stock_count": rng.randint(0, 200),
            "pub_date": f"{year:04d}-01-01T00:00:00Z",
        }
        out.append(rec)
        next_id += 1
    return out


def write_csv(records: list[dict], path: Path) -> None:
    fieldnames = [
        "id", "title", "author", "genres", "language", "year", "pages",
        "rating", "price", "in_stock", "stock_count", "publisher", "isbn",
        "pub_date", "tags", "description",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for rec in records:
            row = dict(rec)
            row["genres"] = ";".join(rec["genres"])
            row["tags"] = ";".join(rec["tags"])
            row["in_stock"] = "true" if rec["in_stock"] else "false"
            writer.writerow(row)


def write_json(records: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)


def main() -> None:
    records = expand(SEED_BOOKS)
    csv_path = DATA_DIR / "books.csv"
    json_path = DATA_DIR / "books.json"
    write_csv(records, csv_path)
    write_json(records, json_path)
    print(f"Wrote {len(records)} records")
    print(f"  CSV : {csv_path}")
    print(f"  JSON: {json_path}")


if __name__ == "__main__":
    main()
