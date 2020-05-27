# These tests are forked from traitlets and adapted to use pytest and to
# test linking traits in addition to traitlets.

import traits.api as t
import pytest

from link_traits import dlink, link, has_traits, has_traitlets


class _A(t.HasTraits):
    value = t.Int(t.Undefined)
    count = t.Int()
try:
    import traitlets

    class _B(traitlets.HasTraits):
        value = traitlets.Int()
        count = traitlets.Int()
    ab = ((_A, _A), (_A, _B), (_B, _A), (_B, _B))
except ImportError:
    ab = ((_A, _A),)
    _B = _A


class TestLinkBidirectional:

    @pytest.mark.parametrize("A, B", ab)
    def test_connect_same(self, A, B):
        """Verify two traitlets of the same type can be linked together using link."""

        a = A(value=9)
        b = B(value=8)

        # Conenct the two classes.
        c = link((a, 'value'), (b, 'value'))

        # Make sure the values are the same at the point of linking.
        assert a.value == b.value

        # Change one of the values to make sure they stay in sync.
        a.value = 5
        assert a.value == b.value
        b.value = 6
        assert a.value == b.value

    def test_connect_same_trait_source_undefined(self, A=_A, B=_B):
        """Verify two traitlets of the same type can be linked together using link."""

        a = A() # a.value is Undefined
        b = B(value=8)

        # Conenct the two classes.
        c = link((a, 'value'), (b, 'value'))
        # Linking doesn't change b.value because a.value is undefined
        assert b.value == 8

        # Change one of the values to make sure they stay in sync.
        a.value = 5
        assert a.value == b.value
        b.value = 6
        assert a.value == b.value
        del a.value # Reset trait (to Undefined in this case)
        if has_traitlets(b):
            # linking sets b.value to 0 if it has traitlets
            assert b.value == 0
        else:
            assert b.value is t.Undefined

    def test_connect_same_trait_target_undefined(self, A=_B, B=_A):
        """Verify two traitlets of the same type can be linked together using link."""

        a = A(value=9)
        b = B() # b.value is Undefined

        # Conenct the two classes.
        c = link((a, 'value'), (b, 'value'))
        assert b.value == 9
        # Change one of the values to make sure they stay in sync.
        a.value = 5
        assert a.value == b.value
        b.value = 6
        assert a.value == b.value
        del b.value # Reset trait (to Undefined in this case)
        if has_traitlets(a):
            # linking sets b.value to 0 if it has traitlets
            assert a.value == 0
        else:
            assert a.value is t.Undefined

    def test_connect_same_trait_target_undefined_source_trait(self, A=_A, B=_A):
        """Verify two traitlets of the same type can be linked together using link."""

        a = A(value=9)
        b = B() # b.value is Undefined

        # Conenct the two classes.
        c = link((a, 'value'), (b, 'value'))
        assert b.value == 9
        # Change one of the values to make sure they stay in sync.
        a.value = 5
        assert a.value == b.value
        b.value = 6
        assert a.value == b.value
        del b.value # Reset trait (to Undefined in this case)
        assert a.value is t.Undefined

    @pytest.mark.parametrize("A, B", ab)
    def test_link_different(self, A, B):
        """Verify two traitlets of different types can be linked together using link."""

        a = A(value=9)
        b = B(count=8)

        # Conenct the two classes.
        c = link((a, 'value'), (b, 'count'))

        # Make sure the values are the same at the point of linking.
        assert a.value == b.count

        # Change one of the values to make sure they stay in sync.
        a.value = 5
        assert a.value == b.count
        b.count = 4
        assert a.value == b.count

    @pytest.mark.parametrize("A, B", ab)
    def test_unlink_link(self, A, B):
        """Verify two linked traitlets can be unlinked."""

        a = A(value=9)
        b = B(value=8)

        # Connect the two classes.
        c = link((a, 'value'), (b, 'value'))
        a.value = 4
        c.unlink()

        # Change one of the values to make sure they don't stay in sync.
        a.value = 5
        assert a.value != b.value
        c.link()
        a.value = b.value
        a.value += 1
        a.value = b.value

    @pytest.mark.parametrize("A, B", ab)
    def test_callbacks(self, A, B):
        """Verify two linked traitlets have their callbacks called once."""

        a = A(value=9)
        b = B(count=8)

        # Register callbacks that count.
        callback_count = []

        def a_callback(name, old, new):
            callback_count.append('a')
        a.on_trait_change(a_callback, 'value')

        def b_callback(name, old, new):
            callback_count.append('b')
        b.on_trait_change(b_callback, 'count')

        # Connect the two classes.
        c = link((a, 'value'), (b, 'count'))

        # Make sure b's count was set to a's value once.
        assert ''.join(callback_count) == 'b'
        del callback_count[:]

        # Make sure a's value was set to b's count once.
        b.count = 5
        assert ''.join(callback_count) == 'ba'
        del callback_count[:]

        # Make sure b's count was set to a's value once.
        a.value = 4
        assert ''.join(callback_count) == 'ab'
        del callback_count[:]

    @pytest.mark.parametrize("A, B", ab)
    def test_tranform(self, A, B):
        """Test transform link."""

        # Create two simple classes with Int traitlets.
        a = A(value=9)
        b = B(value=8)

        # Conenct the two classes.
        c = link((a, 'value'), (b, 'value'),
                 transform=(lambda x: 2 * x, lambda x: int(x / 2.)))

        # Make sure the values are correct at the point of linking.
        b.value = 2 * a.value

        # Change one the value of the source and check that it modifies the target.
        a.value = 5
        b.value = 10
        # Change one the value of the target and check that it modifies the
        # source.
        b.value = 6
        a.value = 3


    @pytest.mark.parametrize("A, B", ab)
    def test_link_broken_at_source(self, A, B):
        a = A()
        b = A()
        dl = dlink((b, "value"), (a, "value"), transform=lambda x: x**2)
        l = link((a, "value"), (b, "value"))
        with pytest.raises(t.TraitError):
            a.value = 2

    @pytest.mark.parametrize("A, B", ab)
    def test_link_broken_at_target(self, A, B):
        a = A()
        b = A()
        dl = dlink((a, "value"), (b, "value"), transform=lambda x: x**2)
        l = link((a, "value"), (b, "value"))
        with pytest.raises(t.TraitError):
            b.value = 2

    def test_no_traits(self, A=_A):
        a = A()
        class B:
            value = 3
        b = B()
        with pytest.raises(ValueError):
            l = link((a, "value"), (b, "value"))
        with pytest.raises(ValueError):
            l = link((b, "value"), (a, "value"))



class TestDirectionalLink:

    @pytest.mark.parametrize("A, B", ab)
    def test_connect_same(self, A, B):
        """Verify two traitlets of the same type can be linked together using dlink."""

        # Create two simple classes with Int traitlets.
        a = A(value=9)
        b = B(value=8)

        # Conenct the two classes.
        c = dlink((a, 'value'), (b, 'value'))

        # Make sure the values are the same at the point of linking.
        assert a.value == b.value

        # Change one the value of the source and check that it synchronizes the
        # target.
        a.value = 5
        assert b.value == 5
        # Change one the value of the target and check that it has no impact on
        # the source
        b.value = 6
        assert a.value == 5

    @pytest.mark.parametrize("A, B", ab)
    def test_tranform(self, A, B):
        """Test transform link."""

        # Create two simple classes with Int traitlets.
        a = A(value=9)
        b = B(value=8)

        # Conenct the two classes.
        c = dlink((a, 'value'), (b, 'value'), lambda x: 2 * x)

        # Make sure the values are correct at the point of linking.
        assert b.value == 2 * a.value

        # Change one the value of the source and check that it modifies the
        # target.
        a.value = 5
        assert b.value == 10
        # Change one the value of the target and check that it has no impact on
        # the source
        b.value = 6
        assert a.value == 5

    @pytest.mark.parametrize("A, B", ab)
    def test_link_different(self, A, B):
        """Verify two traitlets of different types can be linked together using link."""

        a = A(value=9)
        b = B(count=8)

        # Conenct the two classes.
        c = dlink((a, 'value'), (b, 'count'))

        # Make sure the values are the same at the point of linking.
        assert a.value == b.count

        # Change one the value of the source and check that it synchronizes the
        # target.
        a.value = 5
        assert b.count == 5
        # Change one the value of the target and check that it has no impact on
        # the source
        b.value = 6
        assert a.value == 5

    @pytest.mark.parametrize("A, B", ab)
    def test_unlink_link(self, A, B):
        """Verify two linked traitlets can be unlinked."""

        a = A(value=9)
        b = B(value=8)

        # Connect the two classes.
        c = dlink((a, 'value'), (b, 'value'))
        a.value = 4
        c.unlink()

        # Change one of the values to make sure they don't stay in sync.
        a.value = 5
        assert a.value != b.value
        c.link()
        a.value == b.value
        a.value += 1
        a.value == b.value

    def test_connect_same_trait_source_undefined(self, A=_A, B=_B):
        """Verify two traitlets of the same type can be linked together using link."""

        a = A() # a.value is Undefined
        b = B(value=8)

        # Conenct the two classes.
        c = dlink((a, 'value'), (b, 'value'))
        # Linking doesn't change b.value because a.value is undefined
        assert b.value == 8

        # Change one of the values to make sure they stay in sync.
        a.value = 5
        assert a.value == b.value
        b.value = 6
        assert a.value != b.value
        del a.value # Reset trait (to Undefined in this case)
        if has_traitlets(b):
            # linking sets b.value to 0 if it has traitlets
            assert b.value == 0
        else:
            assert b.value is t.Undefined

    def test_connect_same_trait_target_undefined_target_trait(self, A=_A, B=_A):
        """Verify two traitlets of the same type can be linked together using link."""

        a = A()
        b = B(value=9) # b.value is Undefined

        # Conenct the two classes.
        c = dlink((a, 'value'), (b, 'value'))
        assert b.value == 9
        # Change one of the values to make sure they stay in sync.
        a.value = 5
        assert a.value == b.value
        b.value = 6
        assert a.value != b.value
        del a.value # Reset trait (to Undefined in this case)
        assert b.value is t.Undefined

    def test_no_traits(self, A=_A):
        a = A()
        class B:
            value = 3
        b = B()
        with pytest.raises(ValueError):
            l = dlink((b, "value"), (a, "value"))
