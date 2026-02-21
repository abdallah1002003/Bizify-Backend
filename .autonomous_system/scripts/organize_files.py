import os
import shutil
import re

APP_DIR = "app"
MODELS_DIR = os.path.join(APP_DIR, "models")
SCHEMAS_DIR = os.path.join(APP_DIR, "schemas")
ELK_MODELS_DIR = os.path.join(MODELS_DIR, "elk_models")
ELK_SCHEMAS_DIR = os.path.join(SCHEMAS_DIR, "elk_schemas")

# Logical grouping map for models base names
DOMAIN_MAPPING = {
    'auth': ['passwordreset', 'emailverification', 'loginattempt', 'otplog', 'session', 'sessionactivity', 'accountdeletionrequest', 'accountsuspension', 'verfications'],
    'users': ['user', 'userprofile', 'profilechangelog', 'userskill', 'partnerprofile', 'partnerprofilereview', 'coachsessions', 'directory', 'shippingzones'],
    'teams': ['team', 'teammember', 'teaminvitation', 'resourcetransfer', 'invitationhistory', 'role', 'rolechangelog'],
    'ideation': ['idea', 'ideascoring', 'externalidea', 'ideafitlabel', 'ideaattachment', 'ideabudget', 'idearequiredskill', 'ideacollaborator', 'ideaversionhistory', 'ideagenerationbatch', 'ideacomparison', 'comparisonitem', 'comparisonmetric', 'ideachatbotsession'],
    'business': ['business', 'businessroadmap', 'roadmapstage', 'stageupload', 'businessconcept', 'businessstage', 'conceptview', 'businessagentrun', 'businessroadmaptemplate', 'founderreadinessreport', 'workfloworchestrationlog', 'validationconfidencelog'],
    'ai': ['agentrun', 'agentrunconcept', 'aigenerationlog', 'aiprompttemplate', 'analysisqueue'],
    'billing': ['plan', 'subscriptions', 'payments', 'paymentmethod', 'billingaddresses', 'coupons'],
    'core': ['appconfig', 'policy', 'userpolicyacceptance', 'systemrole', 'systemauditlog', 'dailystats', 'industrycategory', 'notes', 'files', 'alert', 'notification', 'notifpreference', 'notificationdeliverylog', 'emaillog'],
    'skills': ['skill', 'skillbenchmark', 'skillgapreport', 'skillgapreportitem'],
    'support': ['contentreport', 'modlogs', 'reviewrequests', 'exportrequest', 'guidestep', 'guideprogress', 'onboardingstep', 'questionnaireresponse'],
    'chat': ['chatsession', 'chatmessage']
}

def get_existing_files(base_dir, ignore_dirs):
    existing = set()
    for root, dirs, files in os.walk(base_dir):
        # Skip elk dirs
        dirs[:] = [d for d in dirs if d not in ignore_dirs and d != '__pycache__']
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                name = file.replace('_', '').replace('.py', '').lower()
                existing.add(name)
    return existing

def clean_and_organize():
    existing_models = get_existing_files(MODELS_DIR, ['elk_models'])
    existing_schemas = get_existing_files(SCHEMAS_DIR, ['elk_schemas'])
    
    print(f"Found {len(existing_models)} existing models constraints.")
    print(f"Found {len(existing_schemas)} existing schema constraints.")
    
    # Process Models
    for file in os.listdir(ELK_MODELS_DIR):
        if not file.endswith('.py'): continue
        name_clean = file.replace('.py', '').lower()
        
        # Check if exists
        if name_clean in existing_models:
            print(f"Deleting duplicate model: {file}")
            os.remove(os.path.join(ELK_MODELS_DIR, file))
            continue
            
        # Move to correct module folder
        target_folder = 'core' # default
        for folder, keywords in DOMAIN_MAPPING.items():
            if name_clean in keywords:
                target_folder = folder
                break
                
        dest_dir = os.path.join(MODELS_DIR, target_folder)
        os.makedirs(dest_dir, exist_ok=True)
        # Create __init__ if needed
        init_file = os.path.join(dest_dir, '__init__.py')
        if not os.path.exists(init_file):
            open(init_file, 'a').close()
            
        shutil.move(os.path.join(ELK_MODELS_DIR, file), os.path.join(dest_dir, file))
        print(f"Moved {file} -> models/{target_folder}/")
        
    # Process Schemas
    for file in os.listdir(ELK_SCHEMAS_DIR):
        if not file.endswith('.py'): continue
        name_clean = file.replace('.py', '').lower()
        
        # Check if exists
        if name_clean in existing_schemas:
            print(f"Deleting duplicate schema: {file}")
            os.remove(os.path.join(ELK_SCHEMAS_DIR, file))
            continue
            
        # Move to correct module folder
        target_folder = 'core' # default
        for folder, keywords in DOMAIN_MAPPING.items():
            if name_clean in keywords:
                target_folder = folder
                break
                
        dest_dir = os.path.join(SCHEMAS_DIR, target_folder)
        os.makedirs(dest_dir, exist_ok=True)
        # Create __init__ if needed
        init_file = os.path.join(dest_dir, '__init__.py')
        if not os.path.exists(init_file):
            open(init_file, 'a').close()
            
        shutil.move(os.path.join(ELK_SCHEMAS_DIR, file), os.path.join(dest_dir, file))
        print(f"Moved {file} -> schemas/{target_folder}/")

    # Clean up empty folders
    if not os.listdir(ELK_MODELS_DIR):
        os.rmdir(ELK_MODELS_DIR)
    if not os.listdir(ELK_SCHEMAS_DIR):
        os.rmdir(ELK_SCHEMAS_DIR)

if __name__ == '__main__':
    clean_and_organize()
    print("Organization Complete.")
