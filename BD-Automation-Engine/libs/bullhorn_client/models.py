"""
Pydantic models for Bullhorn CRM entities.

These mirror the shapes returned / accepted by the Bullhorn REST API
and provide validation + serialisation out of the box.
"""

from typing import Optional

from pydantic import BaseModel, Field


class BullhornCandidate(BaseModel):
    """Bullhorn Candidate entity."""

    id: Optional[int] = None
    firstName: str = ""
    lastName: str = ""
    email: str = ""
    phone: str = ""
    mobile: str = ""
    occupation: str = ""
    companyName: str = ""
    status: str = "Active"
    owner: Optional[str] = None
    customText1: str = ""
    customText2: str = ""
    customText3: str = ""


class BullhornContact(BaseModel):
    """BD-side contact mapped to Bullhorn candidate format.

    Used as an intermediate representation when syncing contacts
    from BD Automation into Bullhorn.
    """

    name: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    title: str = ""
    company: str = ""
    program: str = ""
    linkedin: str = ""

    def to_bullhorn_format(self) -> dict:
        """Convert to the dict format expected by BullhornClient.create_candidate."""
        first = self.first_name
        last = self.last_name
        if not first and self.name:
            parts = self.name.split(None, 1)
            first = parts[0] if parts else ""
            last = parts[1] if len(parts) > 1 else ""

        return {
            "firstName": first,
            "lastName": last,
            "email": self.email,
            "phone": self.phone,
            "occupation": self.title,
            "companyName": self.company,
            "customText1": self.program,
            "customText2": self.linkedin,
            "customText3": "BD-Automation",
            "status": "Active",
        }


class BullhornJobOrder(BaseModel):
    """Bullhorn Job Order entity."""

    id: Optional[int] = None
    title: str = ""
    description: str = ""
    clientCorporation: Optional[str] = None
    status: str = "Open"
    employmentType: str = "Contract"
    address: Optional[str] = None
    dateAdded: Optional[str] = None
    customText1: str = ""  # program name
    customText2: str = ""  # BD score
    customText3: str = ""  # source
