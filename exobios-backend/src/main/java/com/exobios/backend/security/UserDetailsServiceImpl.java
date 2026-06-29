package com.exobios.backend.security;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class UserDetailsServiceImpl implements UserDetailsService {

    // TODO: Inject UserRepository and wire real user lookup after Users module is implemented (Step 5)
    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        throw new UsernameNotFoundException(
                "UserDetailsService not yet implemented — will be wired in Step 5 (Users module).");
    }
}
