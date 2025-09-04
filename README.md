# PgSTAC Event Listener

The purpose of this utility is to listen to PgSTAC events and issue a CloudEvent to
a configured sink.

For now this PoC expects that from inside the postgresql component 
a new event is emitted to the `pgstac_items` channel as per:

```postgresql
create or replace function pgstac.eoepca_notify_item_change()
returns trigger
language plpgsql
as $$
declare
  v_payload text;
begin
  if tg_op = 'DELETE' then
    v_payload := json_build_object(
      'event', tg_op,
      'id', old.id,
      'collection', old.collection,
      'geometry', st_asgeojson(old.geometry)::json,
      'datetime', old.datetime,
      'end_datetime', old.end_datetime
    )::text;
    perform pg_notify('pgstac_items', v_payload);
    return old;
  else
    v_payload := json_build_object(
      'event', tg_op,          -- 'INSERT' sau 'UPDATE'
      'id', new.id,
      'collection', new.collection,
      'geometry', st_asgeojson(new.geometry)::json,
      'datetime', new.datetime,
      'end_datetime', new.end_datetime
    )::text;
    perform pg_notify('pgstac_items', v_payload);
    return new;
  end if;
end;
$$;

drop trigger if exists eoepca_items_notify_change on pgstac.items;
create trigger eoepca_items_notify_change
    after insert or update or delete
    on pgstac.items
    for each row
execute function pgstac.eoepca_notify_item_change();
```

### Caveats

- replacement oparation to the STAC endpoint result in two different events: a deleted and an create event