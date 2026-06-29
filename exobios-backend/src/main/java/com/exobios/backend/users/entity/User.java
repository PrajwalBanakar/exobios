package com.exobios.backend.users.entity;

import com.exobios.backend.common.entity.BaseEntity;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.entity.enums.UserStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

@Entity
@Table(name = "users")
@Getter
@Setter
@NoArgsConstructor
public class User extends BaseEntity {

    @Column(name = "asha_id", unique = true, length = 50)
    private String ashaId;

    @Column(name = "phone", unique = true, nullable = false, length = 20)
    private String phone;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    @Enumerated(EnumType.STRING)
    @Column(name = "role", nullable = false, length = 20)
    private Role role;

    @Column(name = "area", length = 100)
    private String area;

    @Column(name = "district", length = 100)
    private String district;

    @Column(name = "state", length = 100)
    private String state;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private UserStatus status = UserStatus.ACTIVE;

    @Column(name = "last_login_at")
    private Instant lastLoginAt;
}
