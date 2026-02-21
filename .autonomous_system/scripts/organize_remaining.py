import os
import shutil

APP_DIR = "app"
MODELS_DIR = os.path.join(APP_DIR, "models")
SCHEMAS_DIR = os.path.join(APP_DIR, "schemas")

FILE_MAPPING = {
    'admin_invite.py': 'auth',
    'agent_run.py': 'ai',
    'agent_run_concept.py': 'ai',
    'ai_ops.py': 'ai',
    'alert.py': 'core',
    'auth.py': 'auth',
    'billing_address.py': 'billing',
    'coach_session.py': 'users',
    'collaborator.py': 'ideation',
    'concept_definition.py': 'business',
    'coupon.py': 'billing',
    'daily_stats.py': 'core',
    'directory.py': 'users',
    'export_log.py': 'support',
    'file.py': 'core',
    'idea.py': 'ideation',
    'ideation.py': 'ideation',
    'invite.py': 'core',
    'new_collaborator.py': 'ideation',
    'note.py': 'core',
    'notification.py': 'core',
    'payment.py': 'billing',
    'payment_method.py': 'billing',
    'plan.py': 'billing',
    'questionnaire.py': 'support',
    'review.py': 'support',
    'review_request.py': 'support',
    'role.py': 'teams',
    'session.py': 'auth',
    'shipping_zone.py': 'users',
    'subscription.py': 'billing',
    'system.py': 'core',
    'team.py': 'teams',
    'user.py': 'users',
    'user_action.py': 'users',
    'user_guide.py': 'support',
    'user_log.py': 'users',
    'user_profile.py': 'users',
    'verification.py': 'auth',
    'admin.py': 'core',
    'password_recovery.py': 'auth'
}

def move_files(base_dir):
    for file in os.listdir(base_dir):
        # We only care about mapped py files in the root
        if file in FILE_MAPPING and os.path.isfile(os.path.join(base_dir, file)):
            target_folder = FILE_MAPPING[file]
            dest_dir = os.path.join(base_dir, target_folder)
            os.makedirs(dest_dir, exist_ok=True)
            
            init_file = os.path.join(dest_dir, '__init__.py')
            if not os.path.exists(init_file):
                open(init_file, 'a').close()
                
            shutil.move(os.path.join(base_dir, file), os.path.join(dest_dir, file))
            print(f"Moved {file} -> {target_folder}/")

if __name__ == '__main__':
    move_files(MODELS_DIR)
    move_files(SCHEMAS_DIR)
    print("Full organization complete.")
