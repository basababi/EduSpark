from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    email: EmailStr
    role: str | None = None
    track: str | None = None
    interests: list[str] = Field(default_factory=list)
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None


class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    track: str | None = Field(default=None, max_length=20)
    interests: list[str] | None = None
    avatar_url: str | None = Field(default=None, max_length=255)
    locale: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=50)


class UserPreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_notifications: bool
    weekly_report: bool
    daily_reminder: bool
    dark_mode: bool
    compact_view: bool


class UserPreferencesUpdate(BaseModel):
    email_notifications: bool | None = None
    weekly_report: bool | None = None
    daily_reminder: bool | None = None
    dark_mode: bool | None = None
    compact_view: bool | None = None
