package com.exobios.backend.users.controller;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.dto.ChangeStatusRequest;
import com.exobios.backend.users.dto.CreateUserRequest;
import com.exobios.backend.users.dto.UpdateUserRequest;
import com.exobios.backend.users.dto.UserDto;
import com.exobios.backend.users.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "Users", description = "User management — SUPER_ADMIN only, except /me")
public class UserController {

    private final UserService userService;

    @GetMapping
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    @Operation(summary = "List all users — paginated, sorted by createdAt DESC by default")
    public ResponseEntity<ApiResponse<PageResponse<UserDto>>> getAllUsers(
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable) {
        return ResponseEntity.ok(ApiResponse.success(userService.getAllUsers(pageable)));
    }

    @GetMapping("/me")
    @PreAuthorize("isAuthenticated()")
    @Operation(summary = "Get the currently authenticated user's profile")
    public ResponseEntity<ApiResponse<UserDto>> getMe(
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(userService.getUserById(principal.getId())));
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    @Operation(summary = "Get a user by ID")
    public ResponseEntity<ApiResponse<UserDto>> getUserById(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(userService.getUserById(id)));
    }

    @PostMapping
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    @Operation(summary = "Create a new ASHA or SUPER_ADMIN user")
    public ResponseEntity<ApiResponse<UserDto>> createUser(
            @Valid @RequestBody CreateUserRequest request) {
        UserDto created = userService.createUser(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("User created successfully", created));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    @Operation(summary = "Update a user's profile — password is never changed here")
    public ResponseEntity<ApiResponse<UserDto>> updateUser(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateUserRequest request) {
        return ResponseEntity.ok(
                ApiResponse.success("User updated successfully", userService.updateUser(id, request)));
    }

    @PatchMapping("/{id}/status")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    @Operation(summary = "Change a user's status: ACTIVE | INACTIVE | SUSPENDED")
    public ResponseEntity<ApiResponse<UserDto>> changeStatus(
            @PathVariable UUID id,
            @Valid @RequestBody ChangeStatusRequest request) {
        return ResponseEntity.ok(
                ApiResponse.success("Status updated successfully",
                        userService.changeStatus(id, request.getStatus())));
    }
}
