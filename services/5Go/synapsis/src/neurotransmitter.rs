// This file is generated by rust-protobuf 2.25.1. Do not edit
// @generated

// https://github.com/rust-lang/rust-clippy/issues/702
#![allow(unknown_lints)]
#![allow(clippy::all)]

#![allow(unused_attributes)]
#![cfg_attr(rustfmt, rustfmt::skip)]

#![allow(box_pointers)]
#![allow(dead_code)]
#![allow(missing_docs)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(non_upper_case_globals)]
#![allow(trivial_casts)]
#![allow(unused_imports)]
#![allow(unused_results)]
//! Generated file from `neurotransmitter.proto`

/// Generated files are compatible only with the same version
/// of protobuf runtime.
// const _PROTOBUF_VERSION_CHECK: () = ::protobuf::VERSION_2_25_1;

#[derive(PartialEq,Clone,Default)]
pub struct SerializedStuff {
    // message fields
    pub content: ::std::vec::Vec<u8>,
    // special fields
    pub unknown_fields: ::protobuf::UnknownFields,
    pub cached_size: ::protobuf::CachedSize,
}

impl<'a> ::std::default::Default for &'a SerializedStuff {
    fn default() -> &'a SerializedStuff {
        <SerializedStuff as ::protobuf::Message>::default_instance()
    }
}

impl SerializedStuff {
    pub fn new() -> SerializedStuff {
        ::std::default::Default::default()
    }

    // bytes content = 1;


    pub fn get_content(&self) -> &[u8] {
        &self.content
    }
    pub fn clear_content(&mut self) {
        self.content.clear();
    }

    // Param is passed by value, moved
    pub fn set_content(&mut self, v: ::std::vec::Vec<u8>) {
        self.content = v;
    }

    // Mutable pointer to the field.
    // If field is not initialized, it is initialized with default value first.
    pub fn mut_content(&mut self) -> &mut ::std::vec::Vec<u8> {
        &mut self.content
    }

    // Take field
    pub fn take_content(&mut self) -> ::std::vec::Vec<u8> {
        ::std::mem::replace(&mut self.content, ::std::vec::Vec::new())
    }
}

impl ::protobuf::Message for SerializedStuff {
    fn is_initialized(&self) -> bool {
        true
    }

    fn merge_from(&mut self, is: &mut ::protobuf::CodedInputStream<'_>) -> ::protobuf::ProtobufResult<()> {
        while !is.eof()? {
            let (field_number, wire_type) = is.read_tag_unpack()?;
            match field_number {
                1 => {
                    ::protobuf::rt::read_singular_proto3_bytes_into(wire_type, is, &mut self.content)?;
                },
                _ => {
                    ::protobuf::rt::read_unknown_or_skip_group(field_number, wire_type, is, self.mut_unknown_fields())?;
                },
            };
        }
        ::std::result::Result::Ok(())
    }

    // Compute sizes of nested messages
    #[allow(unused_variables)]
    fn compute_size(&self) -> u32 {
        let mut my_size = 0;
        if !self.content.is_empty() {
            my_size += ::protobuf::rt::bytes_size(1, &self.content);
        }
        my_size += ::protobuf::rt::unknown_fields_size(self.get_unknown_fields());
        self.cached_size.set(my_size);
        my_size
    }

    fn write_to_with_cached_sizes(&self, os: &mut ::protobuf::CodedOutputStream<'_>) -> ::protobuf::ProtobufResult<()> {
        if !self.content.is_empty() {
            os.write_bytes(1, &self.content)?;
        }
        os.write_unknown_fields(self.get_unknown_fields())?;
        ::std::result::Result::Ok(())
    }

    fn get_cached_size(&self) -> u32 {
        self.cached_size.get()
    }

    fn get_unknown_fields(&self) -> &::protobuf::UnknownFields {
        &self.unknown_fields
    }

    fn mut_unknown_fields(&mut self) -> &mut ::protobuf::UnknownFields {
        &mut self.unknown_fields
    }

    fn as_any(&self) -> &dyn (::std::any::Any) {
        self as &dyn (::std::any::Any)
    }
    fn as_any_mut(&mut self) -> &mut dyn (::std::any::Any) {
        self as &mut dyn (::std::any::Any)
    }
    fn into_any(self: ::std::boxed::Box<Self>) -> ::std::boxed::Box<dyn (::std::any::Any)> {
        self
    }

    fn descriptor(&self) -> &'static ::protobuf::reflect::MessageDescriptor {
        Self::descriptor_static()
    }

    fn new() -> SerializedStuff {
        SerializedStuff::new()
    }

    fn descriptor_static() -> &'static ::protobuf::reflect::MessageDescriptor {
        static descriptor: ::protobuf::rt::LazyV2<::protobuf::reflect::MessageDescriptor> = ::protobuf::rt::LazyV2::INIT;
        descriptor.get(|| {
            let mut fields = ::std::vec::Vec::new();
            fields.push(::protobuf::reflect::accessor::make_simple_field_accessor::<_, ::protobuf::types::ProtobufTypeBytes>(
                "content",
                |m: &SerializedStuff| { &m.content },
                |m: &mut SerializedStuff| { &mut m.content },
            ));
            ::protobuf::reflect::MessageDescriptor::new_pb_name::<SerializedStuff>(
                "SerializedStuff",
                fields,
                file_descriptor_proto()
            )
        })
    }

    fn default_instance() -> &'static SerializedStuff {
        static instance: ::protobuf::rt::LazyV2<SerializedStuff> = ::protobuf::rt::LazyV2::INIT;
        instance.get(SerializedStuff::new)
    }
}

impl ::protobuf::Clear for SerializedStuff {
    fn clear(&mut self) {
        self.content.clear();
        self.unknown_fields.clear();
    }
}

impl ::std::fmt::Debug for SerializedStuff {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        ::protobuf::text_format::fmt(self, f)
    }
}

impl ::protobuf::reflect::ProtobufValue for SerializedStuff {
    fn as_ref(&self) -> ::protobuf::reflect::ReflectValueRef {
        ::protobuf::reflect::ReflectValueRef::Message(self)
    }
}

#[derive(PartialEq,Clone,Default)]
pub struct AsymmetricKey {
    // message fields
    pub secret: ::protobuf::SingularPtrField<SerializedStuff>,
    pub public_key: ::protobuf::SingularPtrField<SerializedStuff>,
    // special fields
    pub unknown_fields: ::protobuf::UnknownFields,
    pub cached_size: ::protobuf::CachedSize,
}

impl<'a> ::std::default::Default for &'a AsymmetricKey {
    fn default() -> &'a AsymmetricKey {
        <AsymmetricKey as ::protobuf::Message>::default_instance()
    }
}

impl AsymmetricKey {
    pub fn new() -> AsymmetricKey {
        ::std::default::Default::default()
    }

    // .SerializedStuff secret = 1;


    pub fn get_secret(&self) -> &SerializedStuff {
        self.secret.as_ref().unwrap_or_else(|| <SerializedStuff as ::protobuf::Message>::default_instance())
    }
    pub fn clear_secret(&mut self) {
        self.secret.clear();
    }

    pub fn has_secret(&self) -> bool {
        self.secret.is_some()
    }

    // Param is passed by value, moved
    pub fn set_secret(&mut self, v: SerializedStuff) {
        self.secret = ::protobuf::SingularPtrField::some(v);
    }

    // Mutable pointer to the field.
    // If field is not initialized, it is initialized with default value first.
    pub fn mut_secret(&mut self) -> &mut SerializedStuff {
        if self.secret.is_none() {
            self.secret.set_default();
        }
        self.secret.as_mut().unwrap()
    }

    // Take field
    pub fn take_secret(&mut self) -> SerializedStuff {
        self.secret.take().unwrap_or_else(|| SerializedStuff::new())
    }

    // .SerializedStuff public_key = 2;


    pub fn get_public_key(&self) -> &SerializedStuff {
        self.public_key.as_ref().unwrap_or_else(|| <SerializedStuff as ::protobuf::Message>::default_instance())
    }
    pub fn clear_public_key(&mut self) {
        self.public_key.clear();
    }

    pub fn has_public_key(&self) -> bool {
        self.public_key.is_some()
    }

    // Param is passed by value, moved
    pub fn set_public_key(&mut self, v: SerializedStuff) {
        self.public_key = ::protobuf::SingularPtrField::some(v);
    }

    // Mutable pointer to the field.
    // If field is not initialized, it is initialized with default value first.
    pub fn mut_public_key(&mut self) -> &mut SerializedStuff {
        if self.public_key.is_none() {
            self.public_key.set_default();
        }
        self.public_key.as_mut().unwrap()
    }

    // Take field
    pub fn take_public_key(&mut self) -> SerializedStuff {
        self.public_key.take().unwrap_or_else(|| SerializedStuff::new())
    }
}

impl ::protobuf::Message for AsymmetricKey {
    fn is_initialized(&self) -> bool {
        for v in &self.secret {
            if !v.is_initialized() {
                return false;
            }
        };
        for v in &self.public_key {
            if !v.is_initialized() {
                return false;
            }
        };
        true
    }

    fn merge_from(&mut self, is: &mut ::protobuf::CodedInputStream<'_>) -> ::protobuf::ProtobufResult<()> {
        while !is.eof()? {
            let (field_number, wire_type) = is.read_tag_unpack()?;
            match field_number {
                1 => {
                    ::protobuf::rt::read_singular_message_into(wire_type, is, &mut self.secret)?;
                },
                2 => {
                    ::protobuf::rt::read_singular_message_into(wire_type, is, &mut self.public_key)?;
                },
                _ => {
                    ::protobuf::rt::read_unknown_or_skip_group(field_number, wire_type, is, self.mut_unknown_fields())?;
                },
            };
        }
        ::std::result::Result::Ok(())
    }

    // Compute sizes of nested messages
    #[allow(unused_variables)]
    fn compute_size(&self) -> u32 {
        let mut my_size = 0;
        if let Some(ref v) = self.secret.as_ref() {
            let len = v.compute_size();
            my_size += 1 + ::protobuf::rt::compute_raw_varint32_size(len) + len;
        }
        if let Some(ref v) = self.public_key.as_ref() {
            let len = v.compute_size();
            my_size += 1 + ::protobuf::rt::compute_raw_varint32_size(len) + len;
        }
        my_size += ::protobuf::rt::unknown_fields_size(self.get_unknown_fields());
        self.cached_size.set(my_size);
        my_size
    }

    fn write_to_with_cached_sizes(&self, os: &mut ::protobuf::CodedOutputStream<'_>) -> ::protobuf::ProtobufResult<()> {
        if let Some(ref v) = self.secret.as_ref() {
            os.write_tag(1, ::protobuf::wire_format::WireTypeLengthDelimited)?;
            os.write_raw_varint32(v.get_cached_size())?;
            v.write_to_with_cached_sizes(os)?;
        }
        if let Some(ref v) = self.public_key.as_ref() {
            os.write_tag(2, ::protobuf::wire_format::WireTypeLengthDelimited)?;
            os.write_raw_varint32(v.get_cached_size())?;
            v.write_to_with_cached_sizes(os)?;
        }
        os.write_unknown_fields(self.get_unknown_fields())?;
        ::std::result::Result::Ok(())
    }

    fn get_cached_size(&self) -> u32 {
        self.cached_size.get()
    }

    fn get_unknown_fields(&self) -> &::protobuf::UnknownFields {
        &self.unknown_fields
    }

    fn mut_unknown_fields(&mut self) -> &mut ::protobuf::UnknownFields {
        &mut self.unknown_fields
    }

    fn as_any(&self) -> &dyn (::std::any::Any) {
        self as &dyn (::std::any::Any)
    }
    fn as_any_mut(&mut self) -> &mut dyn (::std::any::Any) {
        self as &mut dyn (::std::any::Any)
    }
    fn into_any(self: ::std::boxed::Box<Self>) -> ::std::boxed::Box<dyn (::std::any::Any)> {
        self
    }

    fn descriptor(&self) -> &'static ::protobuf::reflect::MessageDescriptor {
        Self::descriptor_static()
    }

    fn new() -> AsymmetricKey {
        AsymmetricKey::new()
    }

    fn descriptor_static() -> &'static ::protobuf::reflect::MessageDescriptor {
        static descriptor: ::protobuf::rt::LazyV2<::protobuf::reflect::MessageDescriptor> = ::protobuf::rt::LazyV2::INIT;
        descriptor.get(|| {
            let mut fields = ::std::vec::Vec::new();
            fields.push(::protobuf::reflect::accessor::make_singular_ptr_field_accessor::<_, ::protobuf::types::ProtobufTypeMessage<SerializedStuff>>(
                "secret",
                |m: &AsymmetricKey| { &m.secret },
                |m: &mut AsymmetricKey| { &mut m.secret },
            ));
            fields.push(::protobuf::reflect::accessor::make_singular_ptr_field_accessor::<_, ::protobuf::types::ProtobufTypeMessage<SerializedStuff>>(
                "public_key",
                |m: &AsymmetricKey| { &m.public_key },
                |m: &mut AsymmetricKey| { &mut m.public_key },
            ));
            ::protobuf::reflect::MessageDescriptor::new_pb_name::<AsymmetricKey>(
                "AsymmetricKey",
                fields,
                file_descriptor_proto()
            )
        })
    }

    fn default_instance() -> &'static AsymmetricKey {
        static instance: ::protobuf::rt::LazyV2<AsymmetricKey> = ::protobuf::rt::LazyV2::INIT;
        instance.get(AsymmetricKey::new)
    }
}

impl ::protobuf::Clear for AsymmetricKey {
    fn clear(&mut self) {
        self.secret.clear();
        self.public_key.clear();
        self.unknown_fields.clear();
    }
}

impl ::std::fmt::Debug for AsymmetricKey {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        ::protobuf::text_format::fmt(self, f)
    }
}

impl ::protobuf::reflect::ProtobufValue for AsymmetricKey {
    fn as_ref(&self) -> ::protobuf::reflect::ReflectValueRef {
        ::protobuf::reflect::ReflectValueRef::Message(self)
    }
}

static file_descriptor_proto_data: &'static [u8] = b"\
    \n\x16neurotransmitter.proto\"+\n\x0fSerializedStuff\x12\x18\n\x07conten\
    t\x18\x01\x20\x01(\x0cR\x07content\"j\n\rAsymmetricKey\x12(\n\x06secret\
    \x18\x01\x20\x01(\x0b2\x10.SerializedStuffR\x06secret\x12/\n\npublic_key\
    \x18\x02\x20\x01(\x0b2\x10.SerializedStuffR\tpublicKeyJ\xe7\x01\n\x06\
    \x12\x04\0\0\t\x01\n\x08\n\x01\x0c\x12\x03\0\0\x12\n\n\n\x02\x04\0\x12\
    \x04\x02\0\x04\x01\n\n\n\x03\x04\0\x01\x12\x03\x02\x08\x17\n\x0b\n\x04\
    \x04\0\x02\0\x12\x03\x03\x02\x14\n\x0c\n\x05\x04\0\x02\0\x05\x12\x03\x03\
    \x02\x07\n\x0c\n\x05\x04\0\x02\0\x01\x12\x03\x03\x08\x0f\n\x0c\n\x05\x04\
    \0\x02\0\x03\x12\x03\x03\x12\x13\n\n\n\x02\x04\x01\x12\x04\x06\0\t\x01\n\
    \n\n\x03\x04\x01\x01\x12\x03\x06\x08\x15\n\x0b\n\x04\x04\x01\x02\0\x12\
    \x03\x07\x02\x1d\n\x0c\n\x05\x04\x01\x02\0\x06\x12\x03\x07\x02\x11\n\x0c\
    \n\x05\x04\x01\x02\0\x01\x12\x03\x07\x12\x18\n\x0c\n\x05\x04\x01\x02\0\
    \x03\x12\x03\x07\x1b\x1c\n\x0b\n\x04\x04\x01\x02\x01\x12\x03\x08\x02!\n\
    \x0c\n\x05\x04\x01\x02\x01\x06\x12\x03\x08\x02\x11\n\x0c\n\x05\x04\x01\
    \x02\x01\x01\x12\x03\x08\x12\x1c\n\x0c\n\x05\x04\x01\x02\x01\x03\x12\x03\
    \x08\x1f\x20b\x06proto3\
";

static file_descriptor_proto_lazy: ::protobuf::rt::LazyV2<::protobuf::descriptor::FileDescriptorProto> = ::protobuf::rt::LazyV2::INIT;

fn parse_descriptor_proto() -> ::protobuf::descriptor::FileDescriptorProto {
    ::protobuf::Message::parse_from_bytes(file_descriptor_proto_data).unwrap()
}

pub fn file_descriptor_proto() -> &'static ::protobuf::descriptor::FileDescriptorProto {
    file_descriptor_proto_lazy.get(|| {
        parse_descriptor_proto()
    })
}
