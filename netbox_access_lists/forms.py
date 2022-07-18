from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from extras.models import Tag
from dcim.models import Device, Region, Site, SiteGroup
from ipam.models import Prefix
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from utilities.forms import CommentField, DynamicModelChoiceField, DynamicModelMultipleChoiceField, StaticSelectMultiple, TagFilterField
from .models import AccessList, ACLExtendedRule, ACLActionChoices, ACLProtocolChoices, ACLTypeChoices, ACLStandardRule


acl_rule_logic_help = mark_safe('<b>*Note:</b> CANNOT be set if remark is set.')

class AccessListForm(NetBoxModelForm):
    region = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False,
    )
    site_group = DynamicModelMultipleChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        label='Site Group'
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        query_params={
            'region': '$region',
            'group_id': '$site_group',
            'site_id': '$site',
        },
    )
    comments = CommentField()
    tags = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False
    )

    fieldsets = [
        ('Host Details', ('region', 'site_group', 'site', 'device')),
        ('Access-List Details', ('name', 'type', 'default_action', 'tags')),
    ]

    class Meta:
        model = AccessList
        fields = ('region', 'site_group', 'site', 'device', 'name', 'type', 'default_action', 'comments', 'tags')
        help_texts = {
            'default_action': 'The default behavior of the ACL.',
            'name': 'The name uniqueness per device is case insensitive.',
            'type': 'Sets the type of the ACL & its rules.',
        }

    def clean(self):
        cleaned_data = super().clean()
        if self.errors.get('name'):
            return cleaned_data
        name = cleaned_data.get('name')
        device = cleaned_data.get('device')
        if ('name' in self.changed_data or 'device' in self.changed_data) and AccessList.objects.filter(name__iexact=name, device=device).exists():
            raise forms.ValidationError('An ACL with this name (case insensitive) is already associated to this device.')
        return cleaned_data

class AccessListFilterForm(NetBoxModelFilterSetForm):
    model = AccessList
    region = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False,
    )
    site_group = DynamicModelMultipleChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        label='Site Group'
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        query_params={
            'region': '$region',
            'group_id': '$site_group',
            'site_id': '$site',
        },
        required=False
    )
    type = forms.MultipleChoiceField(
        choices=ACLTypeChoices,
        required=False,
        widget=StaticSelectMultiple(),
    )
    default_action = forms.MultipleChoiceField(
        choices=ACLActionChoices,
        required=False,
        widget=StaticSelectMultiple(),
        label='Default Action',
    )
    tag = TagFilterField(model)

    fieldsets = (
        (None, ('q', 'tag')),
        ('Host Details', ('region', 'site_group', 'site', 'device')),
        ('ACL Details', ('type', 'default_action')),
    )


class ACLStandardRuleForm(NetBoxModelForm):
    access_list = DynamicModelChoiceField(
        queryset=AccessList.objects.all(),
        query_params={
            'type': 'standard'
        },
        help_text=mark_safe('<b>*Note:</b> This field will only display Standard ACLs.'),
        label='Access-List',
    )
    source_prefix = DynamicModelChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        help_text=acl_rule_logic_help,
        label='Source Prefix',
    )
    tags = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False
    )

    fieldsets = (
        ('Access-List Details', ('access_list', 'index', 'tags')),
        ('Rule Logic', ('remark', 'action', 'source_prefix')),
    )

    class Meta:
        model = ACLStandardRule
        fields = (
            'access_list', 'index', 'remark', 'action', 'source_prefix',
            'tags',
        )
        help_texts = {
            'action': acl_rule_logic_help,
            'index': 'Determines the order of the rule in the ACL processing.',
            'remark': mark_safe('<b>*Note:</b> CANNOT be set if source prefix OR action is set.'),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('remark'):
            if cleaned_data.get('action'):
                raise forms.ValidationError('Cannot input a remark AND an action. Remove one.')
            if cleaned_data.get('source_prefix'):
                raise forms.ValidationError('Cannot input a remark AND a source prefix. Remove one.')
        #if cleaned_data.get('access_list_type') == 'standard' and (source_ports or destination_prefix or destination_ports):
        #    raise forms.ValidationError('Standard Access-Lists only allow a source_prefix or remark')
        return cleaned_data


class ACLStandardRuleFilterForm(NetBoxModelFilterSetForm):
    model = ACLStandardRule
    access_list = forms.ModelMultipleChoiceField(
        queryset=AccessList.objects.all(),
        required=False,
        widget=StaticSelectMultiple(),
        label='Access-List',
    )
    tag = TagFilterField(model)
    source_prefix = forms.ModelMultipleChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        widget=StaticSelectMultiple(),
        label='Source Prefix',
    )
    action = forms.MultipleChoiceField(
        choices=ACLActionChoices,
        required=False,
        widget=StaticSelectMultiple(),
    )
    fieldsets = (
        (None, ('q', 'tag')),
        ('Rule Details', ('access_list', 'action', 'source_prefix',)),
    )

class ACLExtendedRuleForm(NetBoxModelForm):
    access_list = DynamicModelChoiceField(
        queryset=AccessList.objects.all(),
        query_params={
            'type': 'extended'
        },
        help_text=mark_safe('<b>*Note:</b> This field will only display Extended ACLs.'),
        label='Access-List',
    )
    tags = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False
    )
    source_prefix = DynamicModelChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        help_text=acl_rule_logic_help,
        label='Source Prefix',
    )
    destination_prefix = DynamicModelChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        help_text=acl_rule_logic_help,
        label='Destination Prefix',
    )
    fieldsets = (
        ('Access-List Details', ('access_list', 'index', 'tags')),
        ('Rule Details', ('remark', 'action', 'source_prefix', 'source_ports', 'destination_prefix', 'destination_ports', 'protocol',)),
    )

    class Meta:
        model = ACLExtendedRule
        fields = (
            'access_list', 'index', 'remark', 'action', 'source_prefix',
            'source_ports', 'destination_prefix', 'destination_ports', 'protocol',
            'tags'
        )
        help_texts = {
            'action': acl_rule_logic_help,
            'destination_ports': acl_rule_logic_help,
            'index': 'Determines the order of the rule in the ACL processing.',
            'protocol': acl_rule_logic_help,
            'remark': mark_safe('<b>*Note:</b> CANNOT be set if a prefix, port, OR action is set.'),
            'source_ports': acl_rule_logic_help,
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('remark'):
            if cleaned_data.get('action'):
                raise forms.ValidationError('Cannot input a remark AND an action. Remove one.')
            if cleaned_data.get('source_prefix'):
                raise forms.ValidationError('Cannot input a remark AND a source prefix. Remove one.')
            if cleaned_data.get('source_ports'):
                raise forms.ValidationError('Cannot input a remark AND source ports. Remove one.')
            if cleaned_data.get('destination_prefix'):
                raise forms.ValidationError('Cannot input a remark AND a destination prefix. Remove one.')
            if cleaned_data.get('destination_ports'):
                raise forms.ValidationError('Cannot input a remark AND destination ports. Remove one.')
            if cleaned_data.get('protocol'):
                raise forms.ValidationError('Cannot input a remark AND a protocol. Remove one.')
        #if cleaned_data.get('access_list_type') == 'standard' and (source_ports or destination_prefix or destination_ports):
        #    raise forms.ValidationError('Standard Access-Lists only allow a source_prefix or remark')
        return cleaned_data


class ACLExtendedRuleFilterForm(NetBoxModelFilterSetForm):
    model = ACLExtendedRule
    access_list = forms.ModelMultipleChoiceField(
        queryset=AccessList.objects.all(),
        required=False,
        widget=StaticSelectMultiple(),
        label='Access-List',
    )
    index = forms.IntegerField(
        required=False
    )
    tag = TagFilterField(model)
    action = forms.MultipleChoiceField(
        choices=ACLActionChoices,
        required=False,
        widget=StaticSelectMultiple()
    )
    source_prefix = forms.ModelMultipleChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        widget=StaticSelectMultiple(),
        label='Source Prefix',
    )
    desintation_prefix = forms.ModelMultipleChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        widget=StaticSelectMultiple(),
        label='Destination Prefix',
    )
    protocol = forms.MultipleChoiceField(
        choices=ACLProtocolChoices,
        required=False,
        widget=StaticSelectMultiple()
    )

    fieldsets = (
        (None, ('q', 'tag')),
        ('Rule Details', ('access_list', 'action', 'source_prefix', 'desintation_prefix', 'protocol')),
    )
