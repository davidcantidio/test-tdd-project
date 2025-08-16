"""Test query builder implementation."""

from streamlit_extension.utils.query_builder import (
    QueryBuilder,
    ClientQueryBuilder,
    ProjectQueryBuilder,
    EpicQueryBuilder,
    TaskQueryBuilder,
)


class TestQueryBuilder:
    def test_select_query_building(self):
        """Test SELECT query construction."""
        qb = (
            QueryBuilder("users")
            .select("id", "name")
            .where("age > ?", 18)
            .order_by("name")
            .limit(10)
            .offset(5)
        )
        query, params = qb.build()
        assert (
            query
            == "SELECT id, name FROM users WHERE age > ? ORDER BY name ASC LIMIT 10 OFFSET 5"
        )
        assert params == (18,)

    def test_insert_query_building(self):
        """Test INSERT query construction."""
        qb = QueryBuilder("users").insert(id=1, name="Alice")
        query, params = qb.build()
        assert query == "INSERT INTO users (id, name) VALUES (?, ?)"
        assert params == (1, "Alice")

    def test_update_query_building(self):
        """Test UPDATE query construction."""
        qb = QueryBuilder("users").update(name="Bob").where("id = ?", 1)
        query, params = qb.build()
        assert query == "UPDATE users SET name = ? WHERE id = ?"
        assert params == ("Bob", 1)

    def test_delete_query_building(self):
        """Test DELETE query construction."""
        qb = QueryBuilder("users").delete().where("id = ?", 1)
        query, params = qb.build()
        assert query == "DELETE FROM users WHERE id = ?"
        assert params == (1,)

    def test_join_operations(self):
        """Test JOIN query construction."""
        qb = (
            QueryBuilder("users")
            .select("users.*", "p.name")
            .join("profiles p", "users.id = p.user_id")
            .left_join("orders o", "users.id = o.user_id")
        )
        query, params = qb.build()
        assert (
            query
            == "SELECT users.*, p.name FROM users INNER JOIN profiles p ON users.id = p.user_id LEFT JOIN orders o ON users.id = o.user_id"
        )
        assert params == ()

    def test_parameter_binding(self):
        """Test safe parameter binding."""
        qb = (
            QueryBuilder("users")
            .select("*")
            .where("age > ?", 18)
            .where("name = ?", "Alice")
        )
        query, params = qb.build()
        assert query == "SELECT * FROM users WHERE age > ? AND name = ?"
        assert params == (18, "Alice")

    def test_specialized_builders(self):
        """Test specialized query builders."""
        client_query, client_params = (
            ClientQueryBuilder().active_only().with_project_count().build()
        )
        assert "framework_clients" in client_query
        assert "COUNT(p.id) as project_count" in client_query
        assert client_params == ("active",)

        project_query, project_params = (
            ProjectQueryBuilder()
            .for_client(1)
            .active_only()
            .with_client_info()
            .build()
        )
        assert "framework_clients" in project_query
        assert project_params == (1, "active")

        epic_query, epic_params = (
            EpicQueryBuilder()
            .for_project(2)
            .by_status("open")
            .with_task_stats()
            .build()
        )
        assert "framework_tasks" in epic_query
        assert epic_params == (2, "open")

        task_query, task_params = (
            TaskQueryBuilder()
            .for_epic(3)
            .by_status("pending")
            .with_epic_info()
            .build()
        )
        assert "framework_epics" in task_query
        assert task_params == (3, "pending")
