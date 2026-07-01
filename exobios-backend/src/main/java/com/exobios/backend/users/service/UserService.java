package com.exobios.backend.users.service;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ConflictException;
import com.exobios.backend.users.dto.CreateUserRequest;
import com.exobios.backend.users.dto.UpdateUserRequest;
import com.exobios.backend.users.dto.UserDto;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.entity.enums.UserStatus;
import com.exobios.backend.users.exception.UserNotFoundException;
import com.exobios.backend.users.mapper.UserMapper;
import com.exobios.backend.users.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Pageable;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.exobios.backend.audit.annotation.Auditable;
import com.exobios.backend.audit.entity.enums.AuditAction;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class UserService {

    private final UserRepository  userRepository;
    private final UserMapper      userMapper;
    private final PasswordEncoder passwordEncoder;

    @Auditable(action = AuditAction.CREATE, entityType = "USER")
    @Transactional
    public UserDto createUser(CreateUserRequest request) {
        if (userRepository.existsByPhone(request.getPhone())) {
            throw new ConflictException("Phone number already registered: " + request.getPhone());
        }
        if (request.getRole() == Role.ASHA) {
            if (!StringUtils.hasText(request.getAshaId())) {
                throw new BadRequestException("ASHA ID is required for users with ASHA role");
            }
            if (userRepository.existsByAshaId(request.getAshaId())) {
                throw new ConflictException("ASHA ID already registered: " + request.getAshaId());
            }
        }

        User user = new User();
        user.setName(request.getName());
        user.setPhone(request.getPhone());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setRole(request.getRole());
        user.setAshaId(request.getAshaId());
        user.setArea(request.getArea());
        user.setDistrict(request.getDistrict());
        user.setState(request.getState());
        user.setStatus(UserStatus.ACTIVE);

        User saved = userRepository.save(user);
        log.info("Created user id={} role={}", saved.getId(), saved.getRole());
        return userMapper.toDto(saved);
    }

    public UserDto getUserById(UUID id) {
        return userMapper.toDto(findOrThrow(id));
    }

    public PageResponse<UserDto> getAllUsers(Pageable pageable) {
        return PageResponse.of(userRepository.findAll(pageable).map(userMapper::toDto));
    }

    @Auditable(action = AuditAction.UPDATE, entityType = "USER")
    @Transactional
    public UserDto updateUser(UUID id, UpdateUserRequest request) {
        User user = findOrThrow(id);
        user.setName(request.getName());

        if (StringUtils.hasText(request.getPhone()) && !request.getPhone().equals(user.getPhone())) {
            if (userRepository.existsByPhone(request.getPhone())) {
                throw new ConflictException("Phone number already registered: " + request.getPhone());
            }
            user.setPhone(request.getPhone());
        }

        if (request.getAshaId() != null && !request.getAshaId().equals(user.getAshaId())) {
            if (StringUtils.hasText(request.getAshaId()) && userRepository.existsByAshaId(request.getAshaId())) {
                throw new ConflictException("ASHA ID already registered: " + request.getAshaId());
            }
            user.setAshaId(StringUtils.hasText(request.getAshaId()) ? request.getAshaId() : null);
        }

        if (request.getRole() != null && request.getRole() != user.getRole()) {
            if (request.getRole() == Role.ASHA) {
                String effectiveAshaId = StringUtils.hasText(request.getAshaId())
                        ? request.getAshaId() : user.getAshaId();
                if (!StringUtils.hasText(effectiveAshaId)) {
                    throw new BadRequestException("ASHA ID is required when changing role to ASHA");
                }
            }
            user.setRole(request.getRole());
        }

        user.setArea(request.getArea());
        user.setDistrict(request.getDistrict());
        user.setState(request.getState());

        return userMapper.toDto(userRepository.save(user));
    }

    @Auditable(action = AuditAction.STATUS_CHANGE, entityType = "USER")
    @Transactional
    public UserDto changeStatus(UUID id, UserStatus status) {
        User user = findOrThrow(id);
        user.setStatus(status);
        log.info("Changed user id={} status to {}", id, status);
        return userMapper.toDto(userRepository.save(user));
    }

    public UserDto findByPhone(String phone) {
        return userMapper.toDto(
                userRepository.findByPhone(phone)
                        .orElseThrow(() -> new UserNotFoundException("User not found with phone: " + phone))
        );
    }

    private User findOrThrow(UUID id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException(id));
    }
}
