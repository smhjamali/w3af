'''
BruteforcePlugin.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
import os.path

from itertools import izip, repeat

import core.data.kb.knowledgeBase as kb

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.controllers.bruteforce.bruteforcer import (user_password_bruteforcer,
                                                     password_bruteforcer)
from core.data.request.frFactory import create_fuzzable_requests
from core.data.options.option import option
from core.data.options.optionList import optionList


class BruteforcePlugin(AuditPlugin):
    '''
    This plugin is a superclass for plugins that want to bruteforce any type of login.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AuditPlugin.__init__(self)
        
        # Config params
        self._users_file = os.path.join('core','controllers','bruteforce','users.txt')
        self._passwd_file = os.path.join('core','controllers','bruteforce','passwords.txt')
        self._combo_file = ''
        self._combo_separator = ":"
        self._use_emails = True
        self._use_SVN_users = True
        self._pass_eq_user = True
        self._l337_p4sswd = True
        self._useMails = True
        self._use_profiling = True
        self._profiling_number = 50
        self._stop_on_first = True
                
        # Internal vars
        self._found = False
        self._already_reported = []
        self._already_tested = []

    def _create_user_pass_generator( self, url ):
        up_bf = user_password_bruteforcer(url)
        up_bf.use_emails = self._use_emails
        up_bf.use_profiling = self._use_profiling
        up_bf.profiling_number = self._profiling_number
        up_bf.use_SVN_users = self._use_SVN_users
        up_bf.l337_p4sswd = self._l337_p4sswd
        up_bf.users_file = self._users_file
        up_bf.passwd_file = self._passwd_file
        up_bf.combo_file = self._combo_file
        up_bf.combo_separator = self._combo_separator
        up_bf.pass_eq_user = self._pass_eq_user
        return up_bf.generator()
    
    def _create_pass_generator( self, url ):
        p_bf = password_bruteforcer(url)
        p_bf.use_profiling = self._use_profiling
        p_bf.profiling_number = self._profiling_number
        p_bf.l337_p4sswd = self._l337_p4sswd
        p_bf.passwd_file = self._passwd_file
        return p_bf.generator()

    def bruteforce_wrapper( self, fuzzable_request ):
        self.audit_wrapper( fuzzable_request.copy() )
        
        res = []
        for v in kb.kb.getData( self.getName(), 'auth' ):
            if v.getURL() not in self._already_reported:
                self._already_reported.append( v.getURL() )
                res.extend( create_fuzzable_requests(v['response']) )
        return res
    
    def _bruteforce( self, url, combinations ):
        '''
        @parameter url: A string representation of an URL
        @parameter combinations: A generator with tuples that contain (user,pass)
        '''
        args_iter = izip( repeat(url), combinations )
        self._tm.threadpool.map_multi_args( self._brute_worker, args_iter, chunksize=100 )
    
    def end( self ):
        raise NotImplementedError, ('Bruteforce plugins MUST override the'
                                    ' end() method.')
            
    def _brute_worker( self, url, combination ):
        '''
        This is the method that sends the request to the remote server.
        
        @parameter url: A string representation of an URL
        @parameter combinations: A list of tuples with (user,pass)
        '''
        raise NotImplementedError, ('Bruteforce plugins MUST override method'
                                    ' _bruteWorker.')
        
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        
        d = 'Users file to use in bruteforcing'
        o = option('usersFile', self._users_file, d, 'string')
        ol.add(o)
        
        d = 'Passwords file to use in bruteforcing'
        o = option('passwdFile', self._passwd_file, d, 'string')
        ol.add(o)
        
        d = 'This indicates if we will use usernames from SVN headers collected by w3af plugins in bruteforce.'
        o = option('useSvnUsers', self._use_SVN_users, d, 'boolean')
        ol.add(o)
        
        d = 'This indicates if the bruteforce should stop after finding the first correct user and password.'
        o = option('stopOnFirst', self._stop_on_first, d, 'boolean')
        ol.add(o)
        
        d = 'This indicates if the bruteforce should try password equal user in logins.'
        o = option('passEqUser', self._pass_eq_user, d, 'boolean')
        ol.add(o)
        
        d = 'This indicates if the bruteforce should try l337 passwords'
        o = option('useLeetPasswd', self._l337_p4sswd, d, 'boolean')
        ol.add(o)
        
        d = 'This indicates if the bruteforcer should use emails collected by w3af plugins as users.'
        o = option('useEmails', self._useMails, d, 'boolean')
        ol.add(o)
        
        d = 'This indicates if the bruteforce should use password profiling to collect new passwords.'
        o = option('useProfiling', self._use_profiling, d, 'boolean')
        ol.add(o)
        
        d = 'This indicates how many passwords from profiling will be used.'
        o = option('profilingNumber', self._profiling_number, d, 'integer')
        ol.add(o)
        
        d = 'Combo of username and passord, file to use in bruteforcing'
        o = option('comboFile', self._combo_file, d, 'string')
        ol.add(o)
        
        d = 'Separator string used in Combo file to split username and password'
        o = option('comboSeparator', self._combo_separator, d, 'string')
        ol.add(o)
        
        return ol
        
    def set_options( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._users_file = optionsMap['usersFile'].getValue()
        self._stop_on_first = optionsMap['stopOnFirst'].getValue()
        self._passwd_file = optionsMap['passwdFile'].getValue()
        self._pass_eq_user = optionsMap['passEqUser'].getValue()
        self._l337_p4sswd = optionsMap['useLeetPasswd'].getValue()
        self._use_emails = optionsMap['useEmails'].getValue()
        self._use_SVN_users = optionsMap['useSvnUsers'].getValue()
        self._use_profiling = optionsMap['useProfiling'].getValue()
        self._profiling_number = optionsMap['profilingNumber'].getValue()
        self._combo_file = optionsMap['comboFile'].getValue()
        self._combo_separator = optionsMap['comboSeparator'].getValue()
        

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before
                the current one.
        '''
        return ['grep.password_profiling','grep.get_emails', 'grep.http_auth_detect']

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin bruteforces form authentication logins.
        
        Eleven configurable parameters exist:
            - usersFile
            - stopOnFirst
            - passwdFile
            - passEqUser
            - useLeetPasswd
            - useMailUsers
            - useSvnUsers
            - useMails
            - useProfiling
            - profilingNumber
            - comboFile
            - comboSeparator
        
        This plugin will take users from the file pointed by "usersFile", mail 
        users found on the site ( if "useMailUsers" is set to True ), emails found
        on the site ( if "useMails" is set to True ), and svn users found on the
        site ( if "useSvnUsers" is set to True ).
        
        This plugin will take passwords from the file pointed by "passwdFile"
        and the result of the password profiling plugin ( if "useProfiling" 
        is set to True). The profilingNumber sets the number of results from
        the password profiling plugin to use in the password field.

        This plugin will take a combination of user and password from the
        pointed file by "comboFile". The comboSeparator set the string used to
        split each combination in the comboFile.
        
        The "stopOnFirst" parameter indicates if the bruteforce will stop when
        finding the first valid credentials or not.
        '''
    
    def getType( self ):
        return 'bruteforce'