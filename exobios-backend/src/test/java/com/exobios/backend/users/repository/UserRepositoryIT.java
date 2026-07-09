package com.exobios.backend.users.repository;

import com.exobios.backend.testsupport.AbstractRepositoryIT;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.entity.enums.UserStatus;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataIntegrityViolationException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class UserRepositoryIT extends AbstractRepositoryIT {

    @Autowired
    private UserRepository userRepository;

    private User newUser(String phone, String ashaId, Role role) {
        User u = new User();
        u.setPhone(phone);
        u.setAshaId(ashaId);
        u.setName("Test User");
        u.setPasswordHash("hash");
        u.setRole(role);
        u.setStatus(UserStatus.ACTIVE);
        return u;
    }

    @Test
    void save_persistsAllFieldsAndPopulatesAuditingColumns() {
        User saved = userRepository.saveAndFlush(newUser("9812345670", "ASHA-001", Role.ASHA));

        assertThat(saved.getId()).isNotNull();
        assertThat(saved.getCreatedAt()).isNotNull();
        assertThat(saved.getUpdatedAt()).isNotNull();
        assertThat(saved.getStatus()).isEqualTo(UserStatus.ACTIVE);
    }

    @Test
    void save_withDuplicatePhone_violatesUniqueConstraint() {
        userRepository.saveAndFlush(newUser("9812345671", "ASHA-002", Role.ASHA));
        User duplicate = newUser("9812345671", "ASHA-003", Role.ASHA);

        assertThatThrownBy(() -> userRepository.saveAndFlush(duplicate))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void save_withDuplicateAshaId_violatesUniqueConstraint() {
        userRepository.saveAndFlush(newUser("9812345672", "ASHA-004", Role.ASHA));
        User duplicate = newUser("9812345673", "ASHA-004", Role.ASHA);

        assertThatThrownBy(() -> userRepository.saveAndFlush(duplicate))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void findByPhone_returnsMatchingUser() {
        userRepository.saveAndFlush(newUser("9812345674", "ASHA-005", Role.SUPER_ADMIN));

        assertThat(userRepository.findByPhone("9812345674")).isPresent();
        assertThat(userRepository.findByPhone("0000000000")).isEmpty();
    }

    @Test
    void findByAshaId_returnsMatchingUser() {
        userRepository.saveAndFlush(newUser("9812345675", "ASHA-006", Role.ASHA));

        assertThat(userRepository.findByAshaId("ASHA-006")).isPresent();
        assertThat(userRepository.findByAshaId("ASHA-999")).isEmpty();
    }

    @Test
    void existsByPhone_reflectsPersistedState() {
        userRepository.saveAndFlush(newUser("9812345676", "ASHA-007", Role.ASHA));

        assertThat(userRepository.existsByPhone("9812345676")).isTrue();
        assertThat(userRepository.existsByPhone("1111111111")).isFalse();
    }

    @Test
    void existsByAshaId_reflectsPersistedState() {
        userRepository.saveAndFlush(newUser("9812345677", "ASHA-008", Role.ASHA));

        assertThat(userRepository.existsByAshaId("ASHA-008")).isTrue();
        assertThat(userRepository.existsByAshaId("ASHA-999")).isFalse();
    }
}
