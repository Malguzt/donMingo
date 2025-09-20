from domain.entities.user import User
import pytest

class TestUser:    
    def test_should_fail_when_creating_a_user_with_empty_platform_id(self):
        with pytest.raises(ValueError):
            User(platform_id="", name="John Doe", platform="telegram")

    def test_should_fail_when_creating_a_user_with_empty_platform(self):
        with pytest.raises(ValueError):
            User(platform_id="1", name="John Doe", platform="")

    def test_should_create_a_user_with_empty_name_when_it_is_not_provided(self):
        user = User(platform_id="1", platform="telegram")
        assert user.name == ""
    
    def test_should_return_equal_when_two_users_has_the_same_platform_and_platform_id(self):
        user1 = User(platform_id="1", platform="telegram", name="John Doe")
        user2 = User(platform_id="1", platform="telegram", name="John Doe")
        assert user1 == user2
    
    def test_should_return_equal_when_two_users_has_the_same_platform_and_same_platform_id_but_different_name(self):
        user1 = User(platform_id="1", platform="telegram", name="John Doe")
        user2 = User(platform_id="1", platform="telegram", name="Jane Bon")
        assert user1 == user2
    
    def test_should_return_not_equal_when_two_users_has_different_platform_id(self):
        user1 = User(platform_id="1", platform="telegram", name="John Doe")
        user2 = User(platform_id="2", platform="telegram", name="John Doe")
        assert user1 != user2
    
    def test_should_return_not_equal_when_two_users_has_different_platform(self):
        user1 = User(platform_id="1", platform="telegram", name="John Doe")
        user2 = User(platform_id="1", platform="whatsapp", name="John Doe")
        assert user1 != user2

    def test_should_return_same_hash_when_two_users_has_the_same_platform_and_platform_id(self):
        user1 = User(platform_id="1", platform="telegram", name="John Doe")
        user2 = User(platform_id="1", platform="telegram", name="John Doe")
        assert hash(user1) == hash(user2)
    
    def test_should_return_different_hash_when_two_users_has_different_platform_id(self):
        user1 = User(platform_id="1", platform="telegram", name="John Doe")
        user2 = User(platform_id="2", platform="telegram", name="John Doe")
        assert hash(user1) != hash(user2)
    
    def test_should_return_different_hash_when_two_users_has_different_platform(self):
        user1 = User(platform_id="1", platform="telegram", name="John Doe")
        user2 = User(platform_id="1", platform="whatsapp", name="John Doe")
        assert hash(user1) != hash(user2)