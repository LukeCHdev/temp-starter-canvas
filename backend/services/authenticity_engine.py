# Authenticity validation engine

import logging
from typing import Dict, Any, Tuple
from config.authenticity_levels import AUTHENTICITY_RANKS, VALIDATION_REQUIREMENTS

logger = logging.getLogger(__name__)

class AuthenticityEngine:
    """Engine for validating recipe authenticity."""
    
    def validate_recipe(self, recipe_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate recipe authenticity.
        
        Returns:
            (is_valid, rejection_reason, validation_report)
        """
        validation_report = {
            'checks_performed': [],
            'checks_passed': [],
            'checks_failed': [],
            'warnings': [],
            'special_status': None
        }
        
        # Check for manual override
        if recipe_data.get('manual_override', False):
            validation_report['checks_performed'].append('manual_override')
            validation_report['warnings'].append('Recipe approved via manual override')
            validation_report['special_status'] = 'manual_override'
            return True, '', validation_report
        
        # Check for PAT certification (PRIORITY CHECK)
        from config.authenticity_levels import is_pat_certified, PAT_VALIDATION_RULES
        
        if is_pat_certified(recipe_data):
            validation_report['checks_performed'].append('pat_certification_check')
            validation_report['checks_passed'].append('pat_certification_verified')
            validation_report['special_status'] = 'PAT_CERTIFIED'
            validation_report['warnings'].append('PAT status: strict source requirements relaxed')
            
            # For PAT recipes, ensure rank is 2 (Traditional)
            source_validation = recipe_data.get('source_validation', {})
            if source_validation.get('authenticity_rank') != 2:
                validation_report['warnings'].append('PAT recipes must be rank 2 (Traditional)')
            
            # PAT certification overrides most requirements
            # Only check that basic structure exists
            if not recipe_data.get('authenticity_levels'):
                return False, 'PAT recipe must have authenticity levels structure', validation_report
            
            validation_report['checks_passed'].append('pat_validation_complete')
            return True, '', validation_report
        
        # Check source validation object
        source_validation = recipe_data.get('source_validation', {})
        if not source_validation:
            return False, 'Missing source_validation object', validation_report
        
        validation_report['checks_performed'].append('source_validation_present')
        validation_report['checks_passed'].append('source_validation_present')
        
        # Get authenticity rank
        authenticity_rank = source_validation.get('authenticity_rank')
        if authenticity_rank not in [1, 2, 3]:
            return False, 'Invalid authenticity_rank (must be 1, 2, or 3)', validation_report
        
        validation_report['checks_performed'].append('authenticity_rank_valid')
        validation_report['checks_passed'].append('authenticity_rank_valid')
        
        # Get validation requirements for this rank
        requirements = VALIDATION_REQUIREMENTS.get(authenticity_rank, {})
        
        # Check native language validation
        if requirements.get('requires_native_language', False):
            validation_report['checks_performed'].append('native_language_validation')
            if not source_validation.get('native_language_validated', False):
                validation_report['checks_failed'].append('native_language_validation')
                return False, 'Recipe must be validated in native language', validation_report
            validation_report['checks_passed'].append('native_language_validation')
        
        # Check country domain validation
        if requirements.get('requires_country_domain', False):
            validation_report['checks_performed'].append('country_domain_validation')
            if not source_validation.get('country_domain_validated', False):
                validation_report['checks_failed'].append('country_domain_validation')
                return False, 'Recipe must be validated from country domain', validation_report
            validation_report['checks_passed'].append('country_domain_validation')
        
        # Check official source requirement
        if requirements.get('requires_official_source', False):
            validation_report['checks_performed'].append('official_source_validation')
            if not source_validation.get('official_source', False):
                validation_report['checks_failed'].append('official_source_validation')
                return False, 'Rank 1 recipes must have official source validation', validation_report
            validation_report['checks_passed'].append('official_source_validation')
        
        # Check source references
        source_references = recipe_data.get('source_references', [])
        validation_report['checks_performed'].append('source_references_present')
        if not source_references:
            validation_report['warnings'].append('No source references provided')
        else:
            validation_report['checks_passed'].append('source_references_present')
        
        # Check authenticity levels structure
        authenticity_levels = recipe_data.get('authenticity_levels', [])
        validation_report['checks_performed'].append('authenticity_levels_present')
        if not authenticity_levels or len(authenticity_levels) == 0:
            validation_report['checks_failed'].append('authenticity_levels_present')
            return False, 'Recipe must have at least one authenticity level', validation_report
        validation_report['checks_passed'].append('authenticity_levels_present')
        
        # All validations passed
        return True, '', validation_report

# Global authenticity engine instance
authenticity_engine = AuthenticityEngine()
