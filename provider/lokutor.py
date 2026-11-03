import logging
from collections.abc import Mapping

from dify_plugin import ModelProvider
from dify_plugin.entities.model import ModelType
from dify_plugin.errors.model import CredentialsValidateFailedError

logger = logging.getLogger(__name__)


class LokutorProvider(ModelProvider):
    def validate_provider_credentials(self, credentials: Mapping) -> None:
        try:
            self.get_model_instance(ModelType.TTS).validate_credentials(
                model="versa-2.0", credentials=dict(credentials)
            )
        except CredentialsValidateFailedError:
            raise
        except Exception as ex:
            logger.exception("Lokutor credentials validation failed")
            raise CredentialsValidateFailedError(str(ex)) from ex
