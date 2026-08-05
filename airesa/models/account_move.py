from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _fetch_duplicate_reference(self, matching_states=("draft", "posted")):
        """Drop duplicates the current user is not allowed to read.

        Core resolves duplicates with raw SQL bounded only by company, so it can
        surface moves the current user cannot read (another team's, restricted by
        generic_security_restriction). Filtering them out keeps the restriction the
        module relies on intact instead of granting cross-team access. The access
        check is batched over every duplicate at once (a single query for the whole
        invoice list page) rather than one check per move.
        """
        duplicates = super()._fetch_duplicate_reference(matching_states=matching_states)
        if not duplicates:
            return duplicates
        all_dups = self.browse().union(*duplicates.values())
        allowed = all_dups._filtered_access("read")
        return {move: dups & allowed for move, dups in duplicates.items()}
