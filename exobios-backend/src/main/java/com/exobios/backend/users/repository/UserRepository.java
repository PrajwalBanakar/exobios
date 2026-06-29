package com.exobios.backend.users.repository;

import com.exobios.backend.users.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {

    Optional<User> findByPhone(String phone);

    Optional<User> findByAshaId(String ashaId);

    boolean existsByPhone(String phone);

    boolean existsByAshaId(String ashaId);
}
