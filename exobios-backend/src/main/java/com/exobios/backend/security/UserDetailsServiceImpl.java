package com.exobios.backend.security;

import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.entity.enums.UserStatus;
import com.exobios.backend.users.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserDetailsServiceImpl implements UserDetailsService {

    private final UserRepository userRepository;

    /** Called by DaoAuthenticationProvider during username+password login. The "username" is the phone number. */
    @Override
    public UserDetails loadUserByUsername(String phone) throws UsernameNotFoundException {
        User user = userRepository.findByPhone(phone)
                .orElseThrow(() -> new UsernameNotFoundException("No user found with phone: " + phone));

        return UserPrincipal.from(
                user.getId(),
                user.getPhone(),
                user.getRole().name(),
                user.getStatus() == UserStatus.ACTIVE
        );
    }
}
