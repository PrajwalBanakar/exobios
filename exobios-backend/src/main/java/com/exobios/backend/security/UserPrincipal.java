package com.exobios.backend.security;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

public class UserPrincipal implements UserDetails {

    private final UUID id;
    private final String username;
    private final String role;
    private final boolean enabled;
    private final List<SimpleGrantedAuthority> authorities;

    private UserPrincipal(UUID id, String username, String role, boolean enabled) {
        this.id = id;
        this.username = username;
        this.role = role;
        this.enabled = enabled;
        String normalized = role.startsWith("ROLE_") ? role.substring(5) : role;
        this.authorities = List.of(new SimpleGrantedAuthority("ROLE_" + normalized));
    }

    /** Constructed directly from JWT claims — no database lookup. */
    public static UserPrincipal fromToken(String userId, String role) {
        return new UserPrincipal(UUID.fromString(userId), userId, role, true);
    }

    /** Constructed from a database record — used by UserDetailsServiceImpl (Step 5). */
    public static UserPrincipal from(UUID id, String username, String role, boolean enabled) {
        return new UserPrincipal(id, username, role, enabled);
    }

    public UUID getId() { return id; }
    public String getRole() { return role; }

    @Override public String getUsername() { return username; }
    @Override public String getPassword() { return null; }
    @Override public Collection<? extends GrantedAuthority> getAuthorities() { return authorities; }
    @Override public boolean isEnabled() { return enabled; }
    @Override public boolean isAccountNonExpired() { return true; }
    @Override public boolean isAccountNonLocked() { return true; }
    @Override public boolean isCredentialsNonExpired() { return true; }
}
