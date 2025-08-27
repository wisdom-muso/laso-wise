"""
Custom storage backends for Laso Healthcare
"""
import logging
from whitenoise.storage import CompressedStaticFilesStorage
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)


class ForgivingCompressedStaticFilesStorage(CompressedStaticFilesStorage):
    """
    A custom static files storage that is more forgiving with missing files
    like source maps that might be referenced in JS files but don't exist.
    """
    
    def url(self, name, force=False):
        """
        Override url method to handle missing files gracefully
        """
        try:
            return super().url(name, force)
        except ValueError as e:
            if 'could not be found' in str(e):
                logger.warning(f"Static file not found: {name}. Using original path.")
                # Return the original path if file can't be found
                return super(FileSystemStorage, self).url(name)
            raise
    
    def stored_name(self, name):
        """
        Override stored_name to handle missing files gracefully
        """
        try:
            return super().stored_name(name)
        except ValueError as e:
            if 'could not be found' in str(e):
                logger.warning(f"Static file not found during storage: {name}")
                return name
            raise
    
    def post_process(self, paths, dry_run=False, **options):
        """
        Override post_process to be more forgiving with missing referenced files
        """
        try:
            yield from super().post_process(paths, dry_run, **options)
        except Exception as e:
            if 'could not be found' in str(e) and '.map' in str(e):
                logger.warning(f"Skipping missing source map file: {e}")
                # Continue processing other files
                for path in paths:
                    yield path, None, False
            else:
                raise